#vehicle.py: A class to hold all of our vampire car shenanigans
#Includes a more complex movement system

import direct.directbase.DirectStart #starts drill
from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
from panda3d.physics import BaseParticleEmitter,BaseParticleRenderer
from panda3d.physics import PointParticleFactory,SpriteParticleRenderer
from panda3d.physics import LinearNoiseForce,DiscEmitter
from panda3d.core import TextNode
from panda3d.core import AmbientLight,DirectionalLight
from panda3d.core import Point3,Vec3,Vec4
from panda3d.core import Filename
from direct.particles.Particles import Particles
from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.ForceGroup import ForceGroup
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from panda3d.core import ClockObject

import sys, math, random

MAX_LIGHT = 1.5
BOOSTER_LENGTH = 3
RAMP_INTERVAL_DURATION = 0.25
BOOST_FACTOR = 2.5
BOOST_MAX_SPEED_BONUS = 100
INVULN_TIME = 2.0 

class Vehicle(Actor):
    
    BACKWARDS = -1
    STOPPED = 0
    FORWARDS = 1
    
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    
    def __init__(self, modelStr, driveStr, world, plyr):
        Actor.__init__(self, modelStr, {"drive":driveStr})
        self.world = world
        self.setH(180)
        self.reparentTo(render)
        self.prevtime = 0
        #some movement stats
        self.accel = 30.0
        self.brake = -200.0
        self.deccel = -50.0
        self.bkwdsAccel = -17.5
        self.speed = 0.0
        self.maxSpeed = 260.0
        self.maxBkwdsSpeed = -40.0
        self.direction = Vehicle.STOPPED
        self.isTurning = False
        self.turnFactor = 1.2
        self.loc = ""
        self.rampHprInterval = LerpFunc(self.rampInterval,
                                        fromData=0,
                                        toData=100,
                                        duration=RAMP_INTERVAL_DURATION,
                                        blendType='noBlend',
                                        extraArgs=[(0,0),(0,0)],
                                        name="rampInterval")
        self.health = 100
        self.lastCollision = 0.0
        
            
        
        self.speedClass = Vehicle.LOW
        #Deal with car sounds
        if plyr == "player":
            self.loadSounds()
            self.lowSound.play()
        
    def takeHit(self, entry):
        if ClockObject.getGlobalClock().getLongTime() - self.lastCollision > INVULN_TIME:
            self.lastCollision = ClockObject.getGlobalClock().getLongTime()
            self.health = self.health - 1
            print self.health
    
    def loadSounds(self):
        self.lowSound = base.loader.loadSfx("sound/car_idle.wav")
        self.lowSound.setLoop(True)
        self.mediumSound = base.loader.loadSfx("sound/car_mid.wav")
        self.mediumSound.setLoop(True)
        self.highSound = base.loader.loadSfx("sound/car_high.wav")
        self.highSound.setLoop(True)
    
    def updateEngineSound(self):
        if self.speed < self.maxSpeed / 4 and self.speed > self.maxBkwdsSpeed / 4:
            newSpeed = Vehicle.LOW
        elif self.speed < self.maxSpeed * 3 / 4 and self.speed > self.maxBkwdsSpeed * 3 / 4:
            newSpeed = Vehicle.MEDIUM
        else:
            newSpeed = Vehicle.HIGH
        #Now actually update
        #print "Old speed = %i, New speed = %i"%(self.speedClass, newSpeed)
        if newSpeed != self.speedClass:
            self.speedClass = newSpeed
            if self.speedClass == Vehicle.LOW:
                self.mediumSound.stop()
                self.highSound.stop()
                self.lowSound.play()
            elif self.speedClass == Vehicle.MEDIUM:
                self.lowSound.stop()
                self.highSound.stop()
                self.mediumSound.play()
            else:
                self.mediumSound.stop()
                self.lowSound.stop()
                self.highSound.play()
    
    def setupBooster(self):
        #Booster Stuff
        self.boosters = ParticleEffect()
        self.boosterStartTime = -1
        self.boosterLight = PointLight('boostlight')
        self.boosterLight.setColor(VBase4(0,0,0,1))
        self.boosterLight.setAttenuation(Point3(0,0.001,0.001))
        self.world.boosterLightNP = self.attachNewNode(self.boosterLight)
        self.world.boosterLightNP.setPos(0, 20, 2)
        self.world.boosterLightNP.setHpr(180, 90, 0)
        #self.world.setWorldLight(self)
    
    def addKeyMap(self, keyMap):
        self.keyMap = keyMap
        keyMap["boost"] = 0
        
    def rampInterval(self, t, start, end):
        self.setP(((end[0] - start[0]) * (t / 100)) + start[0])
        self.setR(((end[1] - start[1]) * (t / 100)) + start[1])
        
    #Move: Deals with the frame-by-frame stuff
    def move(self, task):
        elapsed = task.time - self.prevtime
        
        startpos = self.getPos() #Initial position
        wasMoving = self.isTurning or (self.direction != Vehicle.STOPPED)
        
        if self.speed > 0:
            self.direction = Vehicle.FORWARDS
        if self.speed == 0:
            self.direction = Vehicle.STOPPED
        if self.speed < 0:
            self.direction = Vehicle.BACKWARDS
        
        #Deal with turning
        if self.keyMap["left"]:
            self.setH(self.getH() + elapsed * self.speed * self.turnFactor)
            if self.direction != Vehicle.STOPPED:
                self.isTurning = True
        elif self.keyMap["right"]:
            self.setH(self.getH() - elapsed * self.speed * self.turnFactor)
            if self.direction != Vehicle.STOPPED:
                self.isTurning = True
        else:
            self.isTurning = False
        
        #Accelerating
        if (self.keyMap["forward"] and not self.keyMap["backwards"]) or self.keyMap["boost"]:
            if self.direction == Vehicle.BACKWARDS:
                newSpeed = self.speed + (self.accel-self.brake)*elapsed
            else:
                newSpeed = self.speed + self.accel*elapsed
            if newSpeed > self.maxSpeed:
                self.speed = self.maxSpeed
            else:
                self.speed = newSpeed
        
        #Braking/Reversing
        if self.keyMap["backwards"] and not (self.keyMap["forward"] or self.keyMap["boost"]):
            if self.direction == Vehicle.FORWARDS:
                newSpeed = self.speed + (self.bkwdsAccel+self.brake)*elapsed
            else:
                newSpeed = self.speed + self.bkwdsAccel*elapsed
            if newSpeed < self.maxBkwdsSpeed:
                self.speed = self.maxBkwdsSpeed
            else:
                self.speed = newSpeed
        
        #Even if no key is held down, we keep moving!
        if (not self.keyMap["forward"] and not self.keyMap["backwards"] and not self.keyMap["boost"]) or (self.keyMap["forward"] and self.keyMap["backwards"] and self.keyMap["boost"]):
            if self.direction == Vehicle.FORWARDS:
                newSpeed = self.speed + self.deccel*elapsed
            else:
                newSpeed = self.speed - self.deccel*elapsed
            
            if self.direction == Vehicle.FORWARDS:
                if newSpeed < 0:
                    self.speed = 0
                else:
                    self.speed = newSpeed
            if self.direction == Vehicle.BACKWARDS:
                if newSpeed > 0:
                    self.speed = 0
                else:
                    self.speed = newSpeed
        
        #Now actually change position
        if self.direction != Vehicle.STOPPED:
            dist = self.speed * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, self.getZ())
        
        #Next, activate animation if necessary
        isMoving = self.isTurning or (self.direction != Vehicle.STOPPED)
        if not wasMoving and isMoving:
            self.loop("drive")
        elif not isMoving:
            self.stop()
            self.pose("drive", 4)
        
        #Collisions! Yay?
        base.cTrav.traverse(self.world.env)
        #Grab our collision entries
        entries = []
        for i in range(self.world.playerGroundHandler.getNumEntries()):
            entry = self.world.playerGroundHandler.getEntry(i)
            entries.append(entry)
            #print(entry.getIntoNode().getName())
            
        #This code got copied from Roaming Ralph
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(), x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName()[:3] == "lot"):
            self.setZ(entries[0].getSurfacePoint(render).getZ())
            if entries[0].getIntoNode().getName() == "lot_ramp_top":
                if self.loc != entries[0].getIntoNode().getName():
                    slope_angle = math.asin((6 - 3.5) / (-8.845 + 14.923))
                    slope_angle = rad2Deg(math.sin(slope_angle))
                    P = slope_angle * math.cos(deg2Rad(self.getH()))
                    R = slope_angle * -math.sin(deg2Rad(self.getH()))
                    self.rampHprInterval.finish()
                    self.rampHprInterval = LerpFunc(self.rampInterval,
                                                    fromData=0,
                                                    toData=100,
                                                    duration=RAMP_INTERVAL_DURATION,
                                                    blendType='noBlend',
                                                    extraArgs=[(self.getP(),self.getR()),(P,R)],
                                                    name="rampInterval")
                    self.rampHprInterval.start()
                elif not self.rampHprInterval.isPlaying():
                    slope_angle = math.asin((6 - 3.5) / (-8.845 + 14.923))
                    slope_angle = rad2Deg(math.sin(slope_angle))
                    self.setP(slope_angle * math.cos(deg2Rad(self.getH())))
                    self.setR(slope_angle * -math.sin(deg2Rad(self.getH())))
            elif entries[0].getIntoNode().getName() ==  "lot_ramp_bottom":
                if self.loc != entries[0].getIntoNode().getName():
                    slope_angle = math.asin((3.5 - 0) / ( -32.715 - 12.56))
                    slope_angle = rad2Deg(math.sin(slope_angle))
                    P = slope_angle * math.sin(deg2Rad(self.getH()))
                    R = slope_angle * math.cos(deg2Rad(self.getH()))
                    self.rampHprInterval.finish()
                    self.rampHprInterval = LerpFunc(self.rampInterval,
                                                    fromData=0,
                                                    toData=100,
                                                    duration=RAMP_INTERVAL_DURATION,
                                                    blendType='noBlend',
                                                    extraArgs=[(self.getP(),self.getR()),(P,R)],
                                                    name="rampInterval")
                    self.rampHprInterval.start()
                elif not self.rampHprInterval.isPlaying():
                    slope_angle = math.asin((3.5 - 0) / ( -32.715 - 12.56))
                    slope_angle = rad2Deg(math.sin(slope_angle))
                    self.setP(slope_angle * math.sin(deg2Rad(self.getH())))
                    self.setR(slope_angle * math.cos(deg2Rad(self.getH())))
            else:
                if self.loc != entries[0].getIntoNode().getName():
                    self.rampHprInterval = LerpFunc(self.rampInterval,
                                                    fromData=0,
                                                    toData=100,
                                                    duration=RAMP_INTERVAL_DURATION,
                                                    blendType='noBlend',
                                                    extraArgs=[(self.getP(),self.getR()),(0,0)],
                                                    name="rampInterval")
                    self.rampHprInterval.start()
            self.loc = entries[0].getIntoNode().getName()
        #elif (len(entries)>0):
        #    print "Hahahaha, nooope"
        #    self.setPos(startpos)
        
        #Now that actual movement is done, deal with playing the right sound
        self.updateEngineSound()
        
        self.prevtime = task.time
        return Task.cont
    
    def startBoosters(self):
        if self.boosterStartTime == -1:
            self.boosters.loadConfig(Filename('flamethrower4.ptf'))        
            self.boosters.start(self)
            self.boosters.setPos(0, 8.5, 2)
            self.boosters.setHpr(180, 90, 0)
            self.boosters.setLightOff()
            self.maxSpeed = self.maxSpeed + BOOST_MAX_SPEED_BONUS
            self.speed = min(self.speed + 75, self.maxSpeed)
            self.accel = self.accel * BOOST_FACTOR
            self.keyMap["boost"] = 1
            self.boosterLight.setColor(VBase4(MAX_LIGHT,MAX_LIGHT,MAX_LIGHT,1))
            taskMgr.add(self.checkBoosterEnd, "endBoosters")
        
    def checkBoosterEnd(self, task):
        if self.boosterStartTime == -1:
            self.boosterStartTime = task.time
            elapsed = 0
        else:
            elapsed = task.time - self.boosterStartTime
            
        if elapsed > BOOSTER_LENGTH:
            self.boosterLight.setColor(VBase4(0,0,0,1))
            self.boosters.softStop()
            self.accel = self.accel / BOOST_FACTOR
            self.keyMap["boost"] = 0
            self.boosterStartTime = -1
            self.maxSpeed = self.maxSpeed - BOOST_MAX_SPEED_BONUS
            self.speed = min(self.speed, self.maxSpeed)
            return Task.done        
        else:    
            return Task.cont
            
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

import sys, math, random

#WARNING: THESE ARE COPYPASTA'D FROM TUTORIAL8.PY
MAX_LIGHT = 2500
BOOSTER_LENGTH = 3

class Vehicle(Actor):
    
    BACKWARDS = -1
    STOPPED = 0
    FORWARDS = 1
    
    def __init__(self, modelStr, driveStr, world):
        Actor.__init__(self, modelStr, {"drive":driveStr})
        self.world = world
        self.setScale(.005)
        self.setH(180)
        self.reparentTo(render)
        self.prevtime = 0
        #some movement stats
        self.accel = 40.0
        self.deccel = -40.0
        self.bkwdsAccel = -10.0
        self.speed = 0.0
        self.maxSpeed = 100.0
        self.maxBkwdsSpeed = -40.0
        self.direction = Vehicle.STOPPED
        self.isTurning = False
        self.turnFactor = 4.0
    
    def setupBooster(self):
        #Booster Stuff
        self.boosters = ParticleEffect()
        self.boosterStartTime = -1
        self.boosterLight = PointLight('boostlight')
        self.boosterLight.setColor(VBase4(0,0,0,1))
        self.boosterLight.setAttenuation(Point3(0,0.001,0.001))
        self.world.boosterLightNP = self.attachNewNode(self.boosterLight)
        self.world.boosterLightNP.setPos(0, 500, 275)
        self.world.boosterLightNP.setHpr(180, 90, 0)
        self.world.boosterLightNP.setScale(200)
        self.world.setWorldLight(self)
    
    def addKeyMap(self, keyMap):
        self.keyMap = keyMap
        keyMap["boost"] = 0
    
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
                newSpeed = self.speed + (self.accel-self.deccel)*elapsed
            else:
                newSpeed = self.speed + self.accel*elapsed
            if newSpeed > self.maxSpeed:
                self.speed = self.maxSpeed
            else:
                self.speed = newSpeed
        
        #Braking/Reversing
        if self.keyMap["backwards"] and not (self.keyMap["forward"] or self.keyMap["boost"]):
            if self.direction == Vehicle.FORWARDS:
                newSpeed = self.speed + (self.bkwdsAccel+self.deccel)*elapsed
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
        #This code got copied from Roaming Ralph
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(), x.getSurfacePoint(render).getZ()))
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            self.setZ(entries[0].getSurfacePoint(render).getZ())
        elif (len(entries)>0):
            #print "Hahahaha, nooope"
            self.setPos(startpos)
        
        self.prevtime = task.time
        return Task.cont
    
    def startBoosters(self):
        if self.boosterStartTime == -1:
            self.boosters.loadConfig(Filename('flamethrower4.ptf'))        
            self.boosters.start(self)
            self.boosters.setPos(0, 200, 275)
            self.boosters.setHpr(180, 90, 0)
            self.boosters.setScale(200)
            self.boosters.setLightOff()
            self.accel = self.accel * 2
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
            self.accel = self.accel / 2
            self.keyMap["boost"] = 0
            self.boosterStartTime = -1
            return Task.done        
        else:    
            return Task.cont
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

class Vehicle(Actor):
    
    BACKWARDS = -1
    STOPPED = 0
    FORWARDS = 1
    
    def __init__(self, modelStr, driveStr):
        Actor.__init__(self, modelStr, {"drive":driveStr})
        self.setScale(.005)
        self.setH(180)
        self.reparentTo(render)
        self.prevtime = 0
        #some movement stats
        self.accel = 40.0
        self.deccel = -40.0
        self.bkwdsAccel = -40.0
        self.speed = 0.0
        self.maxSpeed = 100.0
        self.direction = Vehicle.STOPPED
        self.isTurning = False
        self.turnFactor = 4.0
    
    def addKeyMap(self, keyMap):
        self.keyMap = keyMap
    
    def move(self, task):
        elapsed = task.time - self.prevtime
        
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
        if self.keyMap["forward"] and not self.keyMap["backwards"]:
            if self.direction == Vehicle.BACKWARDS:
                newSpeed = self.speed + (self.accel-self.deccel)*elapsed
            else:
                newSpeed = self.speed + self.accel*elapsed
            if newSpeed > self.maxSpeed:
                self.speed = self.maxSpeed
            else:
                self.speed = newSpeed
        
        #Braking/Reversing
        if self.keyMap["backwards"] and not self.keyMap["forward"]:
            if self.direction == Vehicle.FORWARDS:
                newSpeed = self.speed + (self.bkwdsAccel+self.deccel)*elapsed
            else:
                newSpeed = self.speed + self.bkwdsAccel*elapsed
            if newSpeed < -self.maxSpeed:
                self.speed = -self.maxSpeed
            else:
                self.speed = newSpeed
        
        #Even if no key is held down, we keep moving!
        if (not self.keyMap["forward"] and not self.keyMap["backwards"]) or (self.keyMap["forward"] and self.keyMap["backwards"]):
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
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
        
        #Next, activate animation if necessary
        isMoving = self.isTurning or (self.direction != Vehicle.STOPPED)
        if not wasMoving and isMoving:
            self.loop("drive")
        elif not isMoving:
            self.stop()
            self.pose("drive", 4)
        
        self.prevtime = task.time
        return Task.cont
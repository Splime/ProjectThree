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
    def __init__(self, modelStr, driveStr):
        Actor.__init__(self, modelStr, {"drive":driveStr})
        self.setScale(.005)
        self.setH(180)
        self.reparentTo(render)
        self.prevtime = 0
        #some movement stats
        self.accel = 20
        self.deccel = -40
        self.speed = 0
        self.maxSpeed = 100
        self.isMovingFwd = False
        self.isMovingBkwd = False
        self.isTurning = False
    
    def addKeyMap(self, keyMap):
        self.keyMap = keyMap
    
    def move(self, task):
        elapsed = task.time - self.prevtime
        
        wasMoving = self.isTurning and self.isMovingFwd and self.isMovingBkwd
        
        if self.speed > 0:
            self.isMovingFwd = True
        if self.speed >= 0:
            self.isMovingBkwd = False
        if self.speed < 0:
            self.isMovingBkwd = True
        if self.speed <= 0:
            self.isMovingFwd = False
        
        # if self.isTurning:
            # print "Turning"
        # if self.isMovingFwd:
            # print "Forward"
        # if self.isMovingBkwd:
            # print "Backwards"
        #Deal with turning
        if self.keyMap["left"]:
            self.setH(self.getH() + elapsed * 100)
            self.isTurning = True
        elif self.keyMap["right"]:
            self.setH(self.getH() - elapsed * 100)
            self.isTurning = True
        else:
            self.isTurning = False
        
        if self.keyMap["forward"] and not self.keyMap["backwards"]:
            #print "Accel Code, speed = %i"%self.speed
            #Calculate a new speed
            newSpeed = self.speed + self.accel*elapsed
            if newSpeed > self.maxSpeed:
                self.speed = self.maxSpeed
            else:
                self.speed = newSpeed
            dist = self.speed * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
            
        if self.keyMap["backwards"] and not self.keyMap["forward"]:
            #print "Backwards Accel Code, speed = %i"%self.speed
            #Calculate a new speed
            newSpeed = self.speed + self.deccel*elapsed
            if newSpeed < -self.maxSpeed:
                self.speed = -self.maxSpeed
            else:
                self.speed = newSpeed
            dist = (self.speed) * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
        
        #Even if no key is held down, we keep moving!
        if (not self.keyMap["forward"] and not self.keyMap["backwards"]) or (self.keyMap["forward"] and self.keyMap["backwards"]):
            #print "Deccel Code, speed = %i"%self.speed
            #Calculate a new speed
            if self.isMovingFwd:
                newSpeed = self.speed + self.deccel*elapsed
            else:
                newSpeed = self.speed - self.deccel*elapsed
            
            if self.isMovingFwd:
                if newSpeed < 0:
                    self.speed = 0
                else:
                    self.speed = newSpeed
            if self.isMovingBkwd:
                if newSpeed > 0:
                    self.speed = 0
                else:
                    self.speed = newSpeed
            dist = (-self.speed / 2) * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * -math.sin(angle)
            dy = dist * math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
        
        #Next, activate animation if necessary
        isMoving = self.isTurning and self.isMovingFwd and self.isMovingBkwd
        if not wasMoving and isMoving:
            self.loop("drive")
        else:
            self.stop()
            self.pose("drive", 4)
        
        self.prevtime = task.time
        return Task.cont
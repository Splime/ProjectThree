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
        self.accel = 1
        self.speed = 4
        self.max_speed = 20
        self.isMoving = False
    
    def addKeyMap(self, keyMap):
        self.keyMap = keyMap
    
    def move(self, task):
        elapsed = task.time - self.prevtime
        #camera.lookAt(self.player)
        if self.keyMap["left"]:
            self.setH(self.getH() + elapsed * 100)
        if self.keyMap["right"]:
            self.setH(self.getH() - elapsed * 100)
        if self.keyMap["forward"] and not self.keyMap["backwards"]:
            dist = self.speed * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
        if self.keyMap["backwards"] and not self.keyMap["forward"]:
            dist = (self.speed / 2) * elapsed
            angle = deg2Rad(self.getH())
            dx = dist * -math.sin(angle)
            dy = dist * math.cos(angle)
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
            
        if self.keyMap["left"] or self.keyMap["right"] or self.keyMap["forward"] or self.keyMap["backwards"]:
            if self.isMoving == False:
                self.isMoving = True
                self.loop("drive")
        else:
            if self.isMoving:
                self.isMoving = False
                self.stop()
                self.pose("drive", 4)
        
        self.prevtime = task.time
        return Task.cont
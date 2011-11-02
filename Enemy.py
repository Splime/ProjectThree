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

class Enemy(DirectObject):
    def __init__(self, startingNode, nodePath, x, y, z ):
        
        self.lastNode = startingNode
        self.currentNode = None
        self.nodePath = nodePath
        
        self.model = Actor("models/panda-model", {"drive":"panda-walk4"})
        self.model.setScale(.005)
        self.model.setH(180)
        self.model.setPos(x,y,z)
        self.model.reparentTo(render)
        
    def move(self, task, map):
        elapsed = task.time - self.prevtime
        #camera.lookAt(self.drill)
        if self.keyMap["left"]:
            self.drill.setH(self.drill.getH() + elapsed * 100)
        if self.keyMap["right"]:
            self.drill.setH(self.drill.getH() - elapsed * 100)
        if self.keyMap["forward"] and not self.keyMap["backwards"]:
            dist = 8 * elapsed
            angle = deg2Rad(self.drill.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.drill.setPos(self.drill.getX() + dx, self.drill.getY() + dy, 0)
        if self.keyMap["backwards"] and not self.keyMap["forward"]:
            dist = 4 * elapsed
            angle = deg2Rad(self.drill.getH())
            dx = dist * -math.sin(angle)
            dy = dist * math.cos(angle)
            self.drill.setPos(self.drill.getX() + dx, self.drill.getY() + dy, 0)
            
        if self.keyMap["left"] or self.keyMap["right"] or self.keyMap["forward"] or self.keyMap["backwards"]:
            if self.isMoving == False:
                self.isMoving = True
                self.drill.loop("drive")
        else:
            if self.isMoving:
                self.isMoving = False
                self.drill.stop()
                self.drill.pose("drive", 4)
        
        self.prevtime = task.time
        return Task.cont
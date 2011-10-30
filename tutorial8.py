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

class World(DirectObject): #subclassing here is necessary to accept events
    def __init__(self):
        #turn off mouse control, otherwise camera is not repositionable
        base.disableMouse()
        base.enableParticles()
        camera.setPosHpr(0, -15, 7, 0, -15, 0)
        self.loadModels()
        #self.setupLights()
        self.setupCollisions()
        render.setShaderAuto() #you probably want to use this
        self.keyMap = {"left":0, "right":0, "forward":0}
        taskMgr.add(self.move, "moveTask")
        self.prevtime = 0
        self.isMoving = False
        self.accept("escape", sys.exit)
        self.accept("arrow_up", self.setKey, ["forward", 1])
        self.accept("w", self.setKey, ["forward", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("d", self.setKey, ["right", 1])
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("a", self.setKey, ["left", 1])
        self.accept("arrow_up-up", self.setKey, ["forward", 0])
        self.accept("w-up", self.setKey, ["forward", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])
        self.accept("d-up", self.setKey, ["right", 0])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("a-up", self.setKey, ["left", 0])
        self.accept("space", self.startShoot)
        self.accept("space-up", self.stopShoot)
        self.accept("ate-smiley", self.eat)
        self.p = ParticleEffect()
        
    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def loadModels(self):
        """loads models into the world"""
        #eat no longer exists? Phooey
        self.drill = Actor("models/panda-model", {"drive":"panda-walk4"})
        self.drill.setScale(.005)
        self.drill.setH(180)
        self.drill.reparentTo(render)
        self.env = loader.loadModel("models/environment")
        self.env.reparentTo(render)
        self.env.setScale(.25)
        self.env.setPos(-8, 42, 0)
        '''
        self.slight = Spotlight('slight')
        self.slight.setColor(VBase4(1, 1, 1, 1))
        self.slnp = self.drill.attachNewNode(self.slight)
        self.slnp.setPos(0.000, -2.150, 4.600)
        self.slnp.setHpr(0, 120, 0)
        self.slnp.setPos(10, 20, 0)
        render.setLight(self.slnp)
        '''
        
        #load targets
        self.targets = []
        for i in range (10):
            target = loader.loadModel("smiley")
            target.setScale(.5)
            target.setPos(random.uniform(-20, 20), random.uniform(-15, 15), 2)
            target.reparentTo(render)
            self.targets.append(target)
        
    def setupLights(self):
        #ambient light
        self.ambientLight = AmbientLight("ambientLight")
        #four values, RGBA (alpha is largely irrelevent), value range is 0:1
        self.ambientLight.setColor((.25, .25, .25, 1))
        self.ambientLightNP = render.attachNewNode(self.ambientLight)
        #the nodepath that calls setLight is what gets illuminated by the light
        render.setLight(self.ambientLightNP)
        #call clearLight() to turn it off
        
        self.keyLight = DirectionalLight("keyLight")
        self.keyLight.setColor((.6,.6,.6, 1))
        self.keyLightNP = render.attachNewNode(self.keyLight)
        self.keyLightNP.setHpr(0, -26, 0)
        render.setLight(self.keyLightNP)
        self.fillLight = DirectionalLight("fillLight")
        self.fillLight.setColor((.4,.4,.4, 1))
        self.fillLightNP = render.attachNewNode(self.fillLight)
        self.fillLightNP.setHpr(30, 0, 0)
        render.setLight(self.fillLightNP)
        
    def drive(self):
        """compound interval for driveing"""
        dist = 5
        angle = deg2Rad(self.drill.getH())
        dx = dist * math.sin(angle)
        dy = dist * -math.cos(angle)
        drilldrive = Parallel(self.drill.posInterval(1, (self.drill.getX() + dx, self.drill.getY() + dy, 0)), \
            self.drill.actorInterval("drive", loop=1, duration=2))
        drilldrive.start()
        #some interval methods:
        # start(), loop(), pause(), resume(), finish()
        # start() can take arguments: start(starttime, endtime, playrate)
        
    def turn(self, direction):
        drillTurn = self.drill.hprInterval(.2, (self.drill.getH() - (10*direction), 0, 0))
        drillTurn.start()
        
    def move(self, task):
        elapsed = task.time - self.prevtime
        camera.lookAt(self.drill)
        if self.keyMap["left"]:
            self.drill.setH(self.drill.getH() + elapsed * 100)
        if self.keyMap["right"]:
            self.drill.setH(self.drill.getH() - elapsed * 100)
        if self.keyMap["forward"]:
            dist = 8 * elapsed
            angle = deg2Rad(self.drill.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.drill.setPos(self.drill.getX() + dx, self.drill.getY() + dy, 0)
            
        if self.keyMap["left"] or self.keyMap["right"] or self.keyMap["forward"]:
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
        
    def setupCollisions(self):
        #instantiates a collision traverser and sets it to the default
        base.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerEvent()
        #set pattern for event sent on collision
        # "%in" is substituted with the name of the into object
        self.cHandler.setInPattern("ate-%in")
        
        cSphere = CollisionSphere((0,0,0), 450) #because the drill is scaled way down
        cNode = CollisionNode("drill")
        cNode.addSolid(cSphere)
        cNode.setIntoCollideMask(BitMask32.allOff()) #drill is *only* a from object
        cNodePath = self.drill.attachNewNode(cNode)
        #cNodePath.show()
        #registers a from object with the traverser with a corresponding handler
        base.cTrav.addCollider(cNodePath, self.cHandler)
        
        for target in self.targets:
            cSphere = CollisionSphere((0,0,0), 2)
            cNode = CollisionNode("smiley")
            cNode.addSolid(cSphere)
            cNodePath = target.attachNewNode(cNode)
            #cNodePath.show()
            
    def startShoot(self):
        self.loadParticleConfig('flamethrower2.ptf')
        
    def stopShoot(self):
        self.p.softStop()
        
    def loadParticleConfig(self, file):
        #Start of the code from steam.ptf
        self.p = ParticleEffect()
        self.p.loadConfig(Filename(file))        
        #Sets particles to birth relative to the teapot, but to render at toplevel
        self.p.start(self.drill)
        self.p.setPos(0, -700, 275)
        #self.p.setPos(0.000, -2.150, 4.600)
        self.p.setHpr(0, 90, 0)
        self.p.setScale(200)
        
    def eat(self, cEntry):
        """handles the drill eating a smiley"""
        #remove target from list of targets
        self.targets.remove(cEntry.getIntoNodePath().getParent())
        #remove from scene graph
        cEntry.getIntoNodePath().getParent().remove()
        
        
        
        
w = World()
run()












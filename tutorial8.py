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

import Node
import Enemy


MAX_LIGHT = 25

class World(DirectObject):
    def __init__(self):
        #turn off mouse control, otherwise camera is not repositionable
        self.lightables = []
        self.cameraPositions = [((0, 5000, 5300), (180, -35, 0)),((0, 3000, 1300), (180, -15, 0))]
        self.cameraIndex = 0
        base.disableMouse()
        base.enableParticles()
        self.setupLights()
        self.loadModels()
        self.setupIntervals()
        camera.reparentTo(self.drill)
        camera.setPosHpr(0, 5000, 5300, 180, -35, 0)
        self.setupCollisions()
        render.setShaderAuto() #you probably want to use this
        self.keyMap = {"left":0, "right":0, "forward":0, "backwards":0}
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
        self.accept("arrow_down", self.setKey, ["backwards", 1])
        self.accept("s", self.setKey, ["backwards", 1])
        
        self.accept("arrow_up-up", self.setKey, ["forward", 0])
        self.accept("w-up", self.setKey, ["forward", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])
        self.accept("d-up", self.setKey, ["right", 0])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("a-up", self.setKey, ["left", 0])
        self.accept("arrow_down-up", self.setKey, ["backwards", 0])
        self.accept("s-up", self.setKey, ["backwards", 0])
        
        self.accept("mouse1", self.startShoot)
        self.accept("mouse1-up", self.stopShoot)
        self.accept("tab", self.shiftCamera)        
        
        self.accept("ate-smiley", self.eat)
        self.p = ParticleEffect()
        
    def setupIntervals(self):
        self.lightOn = LerpFunc(self.lightModify,
                            fromData=0,
                            toData=100,
                            duration=0.2,
                            blendType='noBlend',
                            extraArgs=[True],
                            name="LightUp")
        self.lightOff = LerpFunc(self.lightModify,
                            fromData=0,
                            toData=100,
                            duration=0.2,
                            blendType='noBlend',
                            extraArgs=[False],
                            name="LightDown")
                            
        self.cameraMove = None
    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def setWorldLight(self, object):
        self.lightables.append(object)
        object.setLight(self.keyLightNP)
        object.setLight(self.fillLightNP)
        for light in self.flameLights:
            object.setLight(light[1])
    
    def shiftCamera(self):
        if self.cameraMove:
            self.cameraMove.finish()
        old = self.cameraIndex
        self.cameraIndex += 1
        if self.cameraIndex == len(self.cameraPositions):
            self.cameraIndex = 0
        self.cameraMove=LerpPosHprInterval(camera,
                                            .7, 
                                            self.cameraPositions[self.cameraIndex][0], 
                                            self.cameraPositions[self.cameraIndex][1],
                                            camera.getPos(), 
                                            camera.getHpr())
        self.cameraMove.start()
    
    
    def loadModels(self):
        """loads models into the world"""
        #eat no longer exists? Phooey
        self.drill = Actor("models/panda-model", {"drive":"panda-walk4"})
        self.drill.setScale(.005)
        self.drill.setH(180)
        self.drill.reparentTo(render)
        
        self.flameLights = []
        shadowcam = Spotlight('shadowlight')
        shadowcam.setColor(VBase4(0,0,0,1))
        lens = PerspectiveLens()
        shadowcam.setLens(lens)
        shadowcam.setAttenuation(Point3(0, 0.001, 0.001))
        shadowNP = self.drill.attachNewNode(shadowcam)
        shadowNP.setPos(0, -1400, 450)
        shadowNP.lookAt(self.drill)
        shadowNP.setScale(200)
        shadowNP.node().setShadowCaster(True)
        self.flameLights.append((shadowcam, shadowNP))
        
        for i in range(3):
            slight = PointLight('plight')
            slight.setColor(VBase4(0, 0, 0, 1))
            slight.setAttenuation(Point3(0, 0.001, 0.001))
            slnp = self.drill.attachNewNode(slight)
            slnp.setPos(0, -1200 - (300 * i), 450)
            slnp.setHpr(180, 0, 0)
            slnp.setScale(200)
            self.flameLights.append((slight, slnp))
        
        self.setWorldLight(self.drill)
        
        self.env = loader.loadModel("models/environment")
        self.env.reparentTo(render)
        self.env.setScale(.25)
        self.env.setPos(-8, 42, 0)
        self.setWorldLight(self.env)
        
        #load targets
        self.targets = []
        for i in range (10):
            target = loader.loadModel("smiley")
            target.setScale(.5)
            target.setPos(random.uniform(-20, 20), random.uniform(-15, 15), 2)
            target.reparentTo(render)
            self.targets.append(target)
            self.setWorldLight(target)
         
        # Node Map
        map = Node.NodeMap("nodes.txt")
            
        # enemies    
        self.enemies = []
        file = open('levels/enemies.txt' )
        line = file.readline().rstrip()
        while line != "" :
            nums = line.split(',')
            convertedNums = []
            for i in range(len(nums)):
                if i != 0:
                    convertedNums.append(int(nums[i]))
            nodePos = map.nodeList[int(nums[0])].getPos()
            self.enemies.append( Enemy.Enemy(int(nums[0]), convertedNums, nodePos[0], nodePos[1], nodePos[2] ) )
            line = file.readline().rstrip()
        print "what"
        print str(len(self.enemies))    
        
            
        
    def setupLights(self):
        #ambient light
        self.ambientLight = AmbientLight("ambientLight")
        #four values, RGBA (alpha is largely irrelevent), value range is 0:1
        self.ambientLight.setColor((.10, .10, .10, 1))
        self.ambientLightNP = render.attachNewNode(self.ambientLight)
        #the nodepath that calls setLight is what gets illuminated by the light
        render.setLight(self.ambientLightNP)
        #call clearLight() to turn it off
        
        self.keyLight = DirectionalLight("keyLight")
        self.keyLight.setColor((.20,.20,.20, 1))
        self.keyLightNP = render.attachNewNode(self.keyLight)
        self.keyLightNP.setHpr(0, -26, 0)
        
        self.fillLight = DirectionalLight("fillLight")
        self.fillLight.setColor((.05,.05,.05, 1))
        self.fillLightNP = render.attachNewNode(self.fillLight)
        self.fillLightNP.setHpr(30, 0, 0)
        
    def drive(self):
        """compound interval for driveing"""
        #some interval methods:
        # start(), loop(), pause(), resume(), finish()
        # start() can take arguments: start(starttime, endtime, playrate)
        dist = 5
        angle = deg2Rad(self.drill.getH())
        dx = dist * math.sin(angle)
        dy = dist * -math.cos(angle)
        drilldrive = Parallel(self.drill.posInterval(1, (self.drill.getX() + dx, self.drill.getY() + dy, 0)), \
            self.drill.actorInterval("drive", loop=1, duration=2))
        drilldrive.start()
        
    def turn(self, direction):
        drillTurn = self.drill.hprInterval(.2, (self.drill.getH() - (10*direction), 0, 0))
        drillTurn.start()
        
    def move(self, task):
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
            #cNodePath.show()
            cNodePath = target.attachNewNode(cNode)
    
    def lightModify(self, t, which_way):
        if which_way:
            value = t * MAX_LIGHT
        else:
            value = (100 - t) * MAX_LIGHT
        for light in self.flameLights:
            light[0].setColor(VBase4(value,value,value,1))
        
    def startShoot(self):
        self.loadParticleConfig('flamethrower4.ptf')
        self.lightOff.finish()
        self.lightOn.start()
        
    def stopShoot(self):
        self.p.softStop()
        self.lightOn.finish()
        self.lightOff.start()
        
    def loadParticleConfig(self, file):
        self.p = ParticleEffect()
        self.p.loadConfig(Filename(file))        
        self.p.start(self.drill)
        self.p.setPos(0, -700, 275)
        self.p.setHpr(0, 90, 0)
        self.p.setScale(200)
        self.p.setLightOff()
        
    def eat(self, cEntry):
        """handles the drill eating a smiley"""
        #remove target from list of targets
        self.targets.remove(cEntry.getIntoNodePath().getParent())
        #remove from scene graph
        cEntry.getIntoNodePath().getParent().remove()
        
        
        
w = World()
print "what1"
run()
print "what2"













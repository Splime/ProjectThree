import direct.directbase.DirectStart #starts player
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
from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay
from panda3d.core import AmbientLight,DirectionalLight,LightAttrib
from direct.particles.Particles import Particles
from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.ForceGroup import ForceGroup
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject

import sys, math, random
from vehicle import Vehicle

MAX_LIGHT = 2500
BOOSTER_LENGTH = 3

class World(DirectObject):
    def __init__(self):
        #turn off mouse control, otherwise camera is not repositionable
        self.lightables = []
        self.cameraPositions = [((0, 5000, 5300), (180, -35, 0)),((0, 3000, 1300), (180, -15, 0))]
        self.cameraIndex = 0
        base.disableMouse()
        base.enableParticles()
        self.setupLights()
        self.setupPicking()
        #Prepare the vehicular manslaughter!
        self.player = Vehicle("models/panda-model", "panda-walk4")
        self.loadModels()
        self.setupIntervals()
        camera.reparentTo(self.player)
        camera.setPosHpr(0, 5000, 5300, 180, -35, 0)
        self.setupCollisions()
        render.setShaderAuto() #you probably want to use this
        self.keyMap = {"left":0, "right":0, "forward":0, "backwards":0}
        taskMgr.add(self.player.move, "moveTask")
        
        #Give the vehicle direct access to the keyMap
        self.player.addKeyMap(self.keyMap)
        
        self.prevtime = 0
        self.isMoving = False
        self.speed_norm = 8
        self.speed = self.speed_norm
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
        self.accept("space", self.startBoosters)
        
        self.accept("ate-smiley", self.eat)
        self.p1 = ParticleEffect()
        self.p2 = ParticleEffect()
        self.boosters = ParticleEffect()
        self.boosterStartTime = -1
    
    def setupPicking(self):
        self.picker = CollisionTraverser()
        self.pq     = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
        self.targetRoot = render.attachNewNode('targetRoot')
        self.mouseTask = taskMgr.add(self.mouseTask, 'mouseTask')
    
    def mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            self.picker.traverse(self.targetRoot)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                i = int(self.pq.getEntry(0).getIntoNode().getTag('target'))
                print("Found target: " + str(i))
                  
        return Task.cont
    def startBoosters(self):
        if self.boosterStartTime == -1:
            self.boosters.loadConfig(Filename('flamethrower4.ptf'))        
            self.boosters.start(self.player)
            self.boosters.setPos(0, 200, 275)
            self.boosters.setHpr(180, 90, 0)
            self.boosters.setScale(200)
            self.boosters.setLightOff()
            self.speed = self.speed_norm * 3
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
            self.speed = self.speed_norm
            self.boosterStartTime = -1
            return Task.done        
        else:    
            return Task.cont
   
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
        object.setLight(self.boosterLightNP)
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
        # self.player = Actor("models/panda-model", {"drive":"panda-walk4"})
        # self.player.setScale(.005)
        # self.player.setH(180)
        # self.player.reparentTo(render)
        
        self.flameLights = []
        shadowcam = Spotlight('shadowlight')
        shadowcam.setColor(VBase4(0,0,0,1))
        lens = PerspectiveLens()
        shadowcam.setLens(lens)
        shadowcam.setAttenuation(Point3(0, 0.001, 0.001))
        shadowNP = self.player.attachNewNode(shadowcam)
        shadowNP.setPos(0, -1400, 450)
        shadowNP.lookAt(self.player)
        shadowNP.setScale(200)
        shadowNP.node().setShadowCaster(True)
        self.flameLights.append((shadowcam, shadowNP))
        
        for i in range(2):
            slight = PointLight('plight')
            slight.setColor(VBase4(0, 0, 0, 1))
            slight.setAttenuation(Point3(0, 0.001, 0.001))
            slnp = self.player.attachNewNode(slight)
            slnp.setPos(0, -750 - (950 * i), 450)
            slnp.setHpr(180, 0, 0)
            slnp.setScale(200)
            self.flameLights.append((slight, slnp))
        
        self.boosterLight = PointLight('boostlight')
        self.boosterLight.setColor(VBase4(0,0,0,1))
        self.boosterLight.setAttenuation(Point3(0,0.001,0.001))
        self.boosterLightNP = self.player.attachNewNode(self.boosterLight)
        self.boosterLightNP.setPos(0, 500, 275)
        self.boosterLightNP.setHpr(180, 90, 0)
        self.boosterLightNP.setScale(200)
        self.setWorldLight(self.player)
        
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
            target.reparentTo(self.targetRoot)
            self.targets.append(target)
            self.setWorldLight(target)
        
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
        angle = deg2Rad(self.player.getH())
        dx = dist * math.sin(angle)
        dy = dist * -math.cos(angle)
        playerdrive = Parallel(self.player.posInterval(1, (self.player.getX() + dx, self.player.getY() + dy, 0)), \
            self.player.actorInterval("drive", loop=1, duration=2))
        playerdrive.start()
        
    def setupCollisions(self):
        #instantiates a collision traverser and sets it to the default
        base.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerEvent()
        #set pattern for event sent on collision
        # "%in" is substituted with the name of the into object
        self.cHandler.setInPattern("ate-%in")
        
        cSphere = CollisionSphere((0,0,0), 450) #because the player is scaled way down
        cNode = CollisionNode("player")
        cNode.addSolid(cSphere)
        cNode.setIntoCollideMask(BitMask32.allOff()) #player is *only* a from object
        cNodePath = self.player.attachNewNode(cNode)
        #cNodePath.show()
        #registers a from object with the traverser with a corresponding handler
        base.cTrav.addCollider(cNodePath, self.cHandler)
        i = 0
        for target in self.targets:
            cSphere = CollisionSphere((0,0,0), 2)
            cNode = CollisionNode("smiley")
            cNode.addSolid(cSphere)
            cNode.setIntoCollideMask(BitMask32.bit(1))
            cNode.setTag('target', str(i))
            cNodePath = target.attachNewNode(cNode)
            i += 1
    
    def lightModify(self, t, which_way):
        if which_way: #which_way == true then make it brighter
            value = t/100 * MAX_LIGHT
        else: #which_way == true then make it darker
            value = (100 - t)/100 * MAX_LIGHT
        for light in self.flameLights:
            light[0].setColor(VBase4(value,value,value,1))
        
    def startShoot(self):
        self.loadParticleConfig('flamethrower4.ptf')
        self.lightOff.finish()
        self.lightOn.start()
        
    def stopShoot(self):
        self.p1.softStop()
        self.p2.softStop()
        self.lightOn.finish()
        self.lightOff.start()
        
    def loadParticleConfig(self, file):
        self.p1 = ParticleEffect()
        self.p1.loadConfig(Filename(file))        
        self.p1.start(self.player)
        self.p1.setPos(-250, -700, 275)
        self.p1.setHpr(0, 90, 0)
        self.p1.setScale(200)
        self.p1.setLightOff()
        self.p2 = ParticleEffect()
        self.p2.loadConfig(Filename(file))        
        self.p2.start(self.player)
        self.p2.setPos(250, -700, 275)
        self.p2.setHpr(0, 90, 0)
        self.p2.setScale(200)
        self.p2.setLightOff()
        
    def eat(self, cEntry):
        """handles the player eating a smiley"""
        #remove target from list of targets
        self.targets.remove(cEntry.getIntoNodePath().getParent())
        #remove from scene graph
        cEntry.getIntoNodePath().getParent().remove()
        
        
        
w = World()
run()













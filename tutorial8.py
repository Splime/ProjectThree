from pandac.PandaModules import loadPrcFileData
if 0:
    loadPrcFileData("", "window-title THE_TITLE_GOES_HERE!!!!")
    loadPrcFileData("", "fullscreen 1") # Set to 1 for fullscreen
    loadPrcFileData("", "win-size 1680 1050")
    loadPrcFileData("", "win-origin 0 0")

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

import Node
import Enemy

MAX_LIGHT = 6
BOOSTER_LENGTH = 3
DEBUG = False

class World(DirectObject):
    def __init__(self):
        self.enemyLights = []
        self.cameraPositions = [((0, 95, 75), (180, -27, 0)),((0, 55, 25), (180, -15, 0))]
        self.cameraIndex = 0
        base.disableMouse()
        base.enableParticles()
        self.setupLights()
        self.setupPicking()
        #Prepare the vehicular manslaughter!
        self.boosterLightNP = None
        self.flameLights = None
        self.player = Vehicle("ralph_models/vampire_car", "ralph_models/vampire_car", self)
        
        self.loadModels()
        self.player.setPos(0,0,0)
        self.setupIntervals()
        camera.reparentTo(self.player)
        camera.setPos(self.cameraPositions[0][0][0],self.cameraPositions[0][0][1],self.cameraPositions[0][0][2])
        camera.setHpr(self.cameraPositions[0][1][0],self.cameraPositions[0][1][1],self.cameraPositions[0][1][2])
        self.setupCollisions()
        render.setShaderAuto() #you probably want to use this
        self.keyMap = {"left":0, "right":0, "forward":0, "backwards":0}
        taskMgr.add(self.player.move, "moveTask")
        
        #Give the vehicle direct access to the keyMap
        self.player.addKeyMap(self.keyMap)
        
        #Sounds!
        self.loadSounds()
        
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
        self.accept("space", self.player.startBoosters)
        
        self.accept("ate-smiley", self.eat)
        self.p1 = ParticleEffect()
        self.p2 = ParticleEffect()
        
        #Show collisiony stuff
        if DEBUG:
            base.cTrav.showCollisions(render)
        
        #f = open('testLog.txt', 'r+')
        #self.dfs(file = f)
        
    
        self.setLights()
    
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
        
    def dfs(self, item = render, depth = 0, file = None):
        if file:
            file.write(("-" * depth) + item.getName() + ": \n")
        print(("-" * depth) + item.getName() + ": ")
        for i in range(item.getNumNodes()):
            if file:
                file.write((" " * depth) + "+" + item.getNode(i).getName() + ": " + str(item.getNode(i).getClassType()) + "\n")
            print((" " * depth) + "+" + item.getNode(i).getName() + ": " + str(item.getNode(i).getClassType()))
        for i in range(item.getNumChildren()):
            self.dfs(item.getChild(i), depth + 1, file)
            
    def mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            self.picker.traverse(self.targetRoot)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                i = int(self.pq.getEntry(0).getIntoNode().getTag('target'))
                  
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
        object.setLight(self.keyLightNP)
        object.setLight(self.fillLightNP)
        object.setLight(self.boosterLightNP)
        for light in self.enemyLights:
            object.setLight(light)
        
    def setLights(self):
        self.setWorldLight(self.player)
        self.setWorldLight(self.env)
        for enemy in self.enemies:
            self.setWorldLight(enemy)
        
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
        self.player.setupBooster()
        self.env = loader.loadModel("ralph_models/green_ramps")      
        self.env.reparentTo(render)
        self.env.setScale(15)
        
        #self.setWorldLight(self.env)
        
        #load targets
        #self.targets = []
        #for i in range (10):
            #target = loader.loadModel("smiley")
            #target.setScale(.5)
            #target.setPos(random.uniform(-20, 20), random.uniform(-15, 15), 2)
            #target.reparentTo(self.targetRoot)
            #self.targets.append(target)
            #self.setWorldLight(target)
         
        # Node Map
        map = Node.NodeMap("nodes.txt")
            
        # enemies    
        self.enemies = []
        file = open('levels/enemies.txt' )
        line = file.readline().rstrip()
        i = 0
        while line != "" :
            nums = line.split(',')
            convertedNums = []
            for i in range(len(nums)):
                if i != 0:
                    convertedNums.append(int(nums[i]))
            nodePos = map.nodeList[int(nums[0])].getPos()
            newEnemy = Enemy.Enemy(map, convertedNums, self, nodePos[0], nodePos[1], nodePos[2] )
            self.enemies.append( newEnemy )
            #self.setWorldLight( newEnemy ) 
            taskMgr.add(newEnemy.move, "Enemy Move " + str(i), extraArgs = [map], appendTask = True)
            line = file.readline().rstrip()
            i = i + 1
        
            
    def loadSounds(self):
        self.flamethrowerSound = base.loader.loadSfx("sound/dragonflameloop.wav")
        self.flamethrowerEndSound = base.loader.loadSfx("sound/dragonflameend.wav")
        
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
               
    def setupCollisions(self):       
        base.cTrav = CollisionTraverser() 
        self.playerRay = CollisionRay()
        self.playerRay.setOrigin(0,0,1000)
        self.playerRay.setDirection(0,0,-1)
        self.playerNode = CollisionNode("playerRay")
        self.playerNode.addSolid(self.playerRay)
        self.playerNode.setFromCollideMask(BitMask32.bit(0))
        self.playerNode.setIntoCollideMask(BitMask32.allOff())
        self.playerNodePath = self.player.attachNewNode(self.playerNode)
        self.playerNodePath.show()
        self.playerGroundHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(self.playerNodePath, self.playerGroundHandler)
        
        envcNode1 = CollisionNode("lot_bottom")
        envcNode1.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(12.56, 19.182, 0), Point3(12.56, -21.261, 0),
                                Point3(-13.217, -21.261, 0), Point3(-13.217, 19.182, 0))
        envcNode1.addSolid(temp)
        
        envcNode2 = CollisionNode("lot_ramp_bottom")
        envcNode2.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(32.715, -14.923, 3.5), Point3(32.715, -21.261, 3.5),
                                Point3(12.56, -21.261, 0), Point3(12.56, -14.923, 0))
        envcNode2.addSolid(temp)
        
        envcNode3 = CollisionNode("lot_middle")
        envcNode3.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(42.715, -14.923, 3.5), Point3(42.715, -21.261, 3.5),
                                Point3(32.715, -21.261, 3.5), Point3(32.715, -14.923, 3.5))
        envcNode3.addSolid(temp)
        
        envcNode4 = CollisionNode("lot_ramp_top")
        envcNode4.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(42.715, -8.845, 6), Point3(42.715, -14.923, 3.5),
                                Point3(32.715, -14.923, 3.5), Point3(32.715, -8.845, 6))
        envcNode4.addSolid(temp)
        
        envcNode5 = CollisionNode("lot_top")
        envcNode5.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(42.715, 16.155, 6), Point3(42.715, -8.845, 6),
                                Point3(17.715, -8.845, 6), Point3(17.715, 16.155, 6))
        envcNode5.addSolid(temp)
        
        wallCNode = CollisionNode("fence")
        wallCNode.setFromCollideMask(BitMask32.bit(0))
        temp = CollisionPolygon(Point3(12.56, 19.182, 0), Point3(12.56, -14.923, 0),
                                Point3(12.56, -14.923, 10), Point3(12.56, 19.182, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(12.56, -14.923, 0), Point3(32.715, -14.923, 3.5),
                                Point3(32.715, -14.923, 10), Point3(12.56, -14.923, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(32.715, -14.923, 3.5), Point3(32.715, -8.845, 6),
                                Point3(32.715, -8.845, 10), Point3(32.715, -14.923, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(32.715, -8.845, 6), Point3(17.715, -8.845, 6),
                                Point3(17.715, -8.845, 10), Point3(32.715, -8.845, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(17.715, -8.845, 6), Point3(17.715, 16.155, 6),
                                Point3(17.715, 16.155, 10), Point3(17.715, -8.845, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(17.715, 16.155, 6), Point3(42.715, 16.155, 6),
                                Point3(42.715, 16.155, 10), Point3(17.715, 16.155, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(42.715, 16.155, 6), Point3(42.715, -8.845, 6),
                                Point3(42.715, -8.845, 10), Point3(42.715, 16.155, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(42.715, -8.845, 6), Point3(42.715, -14.923, 3.5),
                                Point3(42.715, -14.923, 10), Point3(42.715, -8.845, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(42.715, -14.923, 3.5), Point3(42.715, -21.261, 3.5),
                                Point3(42.715, -21.261, 10), Point3(42.715, -14.923, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(42.715, -21.261, 3.5), Point3(32.715, -21.261, 3.5),
                                Point3(32.715, -21.261, 10), Point3(42.715, -21.261, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(32.715, -21.261, 3.5), Point3(12.56, -21.261, 0),
                                Point3(12.56, -21.261, 10), Point3(32.715, -21.261, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(12.56, -21.261, 0), Point3(-13.217, -21.261, 0),
                                Point3(-13.217, -21.261, 10), Point3(12.56, -21.261, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(-13.217, -21.261, 0), Point3(-13.217, 19.182, 0),
                                Point3(-13.217, 19.182, 10), Point3(-13.217, -21.261, 10))
        wallCNode.addSolid(temp)
        temp = CollisionPolygon(Point3(-13.217, 19.182, 0), Point3(12.56, 19.182, 0),
                                Point3(12.56, 19.182, 10), Point3(-13.217, 19.182, 10))
        wallCNode.addSolid(temp)
        
        
        envcNodePath1 = self.env.attachNewNode(envcNode1)
        envcNodePath2 = self.env.attachNewNode(envcNode2)
        envcNodePath3 = self.env.attachNewNode(envcNode3)
        envcNodePath4 = self.env.attachNewNode(envcNode4)
        envcNodePath5 = self.env.attachNewNode(envcNode5)
        
        self.cHandler = CollisionHandlerEvent()
        pusher = CollisionHandlerPusher()
        
        self.wallNode = self.env.attachNewNode('wallNode')
        wallCNodePath = self.wallNode.attachNewNode(wallCNode)
        if DEBUG:
            wallCNodePath.show()
        
        segment1 = CollisionSegment(-4, -10, 2,  4, -10, 2)
        segment2 = CollisionSegment(-4,   9, 2,  4,   9, 2)
        segment3 = CollisionSegment(-4, -10, 2, -4,   9, 2)
        segment4 = CollisionSegment( 4, -10, 2,  4,   9, 2)
        
        cNode = CollisionNode("player")
        #cNode.addSolid(segment1)
        #cNode.addSolid(segment2)
        #cNode.addSolid(segment3)
        #cNode.addSolid(segment4)
        temp = CollisionSphere((0,-5.5,10), 4)
        cNode.addSolid(temp)
        temp = CollisionSphere((0,-0.5,10), 4)
        cNode.addSolid(temp)
        temp = CollisionSphere((0,3.5,10), 4)
        cNode.addSolid(temp)
        cNode.setIntoCollideMask(BitMask32.allOff()) #player is *only* a from object
        cNodePath = self.player.attachNewNode(cNode)
        if DEBUG:
            cNodePath.show()
            
        base.cTrav.addCollider(cNodePath, pusher)
        pusher.addCollider(cNodePath, self.player)
        pusher.addInPattern('%fn-into-%in')
        self.accept('player-into-fence', self.collideWithFence)
        #registers a from object with the traverser with a corresponding handler
        #base.cTrav.addCollider(cNodePath, self.cHandler)
        # i = 0
        # for target in self.targets:
            # cSphere = CollisionSphere((0,0,0), 2)
            # cNode = CollisionNode("smiley")
            ##cNode.addSolid(cSphere)
            # cNode.setIntoCollideMask(BitMask32.bit(1))
            # cNode.setTag('target', str(i))
            # cNodePath = target.attachNewNode(cNode)
            # i += 1
            
        for enemy in self.enemies:
            lightRay = CollisionRay()
            lightRay.setOrigin(0, -2, 10)
            
            # This is assumed based on the -175 degree pitch of the headlights.
            lightRay.setDirection( 1 , 0 , -0.875 ) 
            lightRayNode = CollisionNode("lightRay")
            lightRayNode.addSolid(lightRay)
            lightRayNode.setIntoCollideMask(BitMask32.allOff())
            lightRayNodePath = enemy.attachNewNode(lightRayNode)
            lightRayNodePath.show()

    
    def collideWithFence(self, entry):
        self.player.speed = self.player.speed * 0.9
        
    def lightModify(self, t, which_way):

        if which_way: #which_way == true then make it brighter
            value = t/100 * MAX_LIGHT
        else: #which_way == true then make it darker
            value = (100 - t)/100 * MAX_LIGHT
        for light in self.flameLights:
            light[0].setColor(VBase4(value,value,value,1))
        
    def startShoot(self):
        self.loadParticleConfig('flamethrower6.ptf')
        #self.lightOff.finish()
        #self.lightOn.start()
        
        #Get the flame noise started!
        self.flamethrowerSound.setLoop(True)
        self.flamethrowerSound.play()
        
    def stopShoot(self):
        self.p1.softStop()
        self.p2.softStop()
        #self.lightOn.finish()
        #self.lightOff.start()
        
        self.flamethrowerSound.stop()
        self.flamethrowerEndSound.play()
        
    def loadParticleConfig(self, file):
        self.p1.reset()
        self.p1 = ParticleEffect()
        self.p1.loadConfig(Filename(file))        
        self.p1.start(self.player)
        self.p1.setPos(-1.75, -10, 1.375)
        self.p1.setHpr(0, 90, 0)
        self.p1.setScale(1.5)
        self.p1.setLightOff()
        self.p2.reset()
        self.p2 = ParticleEffect()
        self.p2.loadConfig(Filename(file))        
        self.p2.start(self.player)
        self.p2.setPos(1.75, -10, 1.375)
        self.p2.setHpr(0, 90, 0)
        self.p2.setScale(1.5)
        self.p2.setLightOff()
        
    def eat(self, cEntry):
        """handles the player eating a smiley"""
        #remove target from list of targets
        self.targets.remove(cEntry.getIntoNodePath().getParent())
        #remove from scene graph
        cEntry.getIntoNodePath().getParent().remove()
        
        
        
w = World()
run()













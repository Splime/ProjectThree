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

import math
import vehicle

LEEWAY = 0.5
ANGLE_LEEWAY = 1.0

STUN_LENGTH = 4.0

MOVING = 0
TURNING = 1
STOPPED = 2

class Enemy(vehicle.Vehicle):
    def __init__(self, map, nodePath, world, x, y, z ):
        vehicle.Vehicle.__init__(self, "ralph_models/drone-model", "ralph_models/drone-model", world, None)
        self.setPos(x,y,z)
        self.nodePath = nodePath
        
        self.curNodeIndex = 0 
        self.speed = 40.0
        
        self.firstNode = nodePath[0]
        
        self.turnSpeed = 80.0
        
        self.phase = TURNING
        
        self.lastNodePos = map.nodeList[nodePath[self.curNodeIndex]].getPos()
        self.nextNodePos = map.nodeList[nodePath[self.curNodeIndex+1]].getPos()
        
        self.finishedTurning = True
        
        
        self.headlight1 = Spotlight('headlight1')
        self.headlight1.setColor(VBase4(75, 75, 75, 75))
        self.headlight1.setAttenuation(Point3(0,0.001,0.001))
        self.lens = PerspectiveLens()
        self.headlight1.setLens(self.lens)
        self.headlight1NP = self.attachNewNode(self.headlight1)
        self.headlight1NP.setPos(0, -2, 2)
        self.headlight1NP.setHpr(0,-175, 0)
        self.headlight1.getLens().setFov(180)
        
        self.headlight1.getLens().setFar(10)
        #self.headlight1.getLens().setFilmSize(50,50)
        #self.headlight1NP.lookAt(0,0,0)
        #self.headlight1.showFrustum()
        self.world.enemyLights.append(self.headlight1NP)
        #self.world.setWorldLight(self)
        
        
        
    def turn( self, task ):
        elapsed = task.time - self.prevtime
        dx = self.lastNodePos[0] - self.nextNodePos[0]
        dy = self.lastNodePos[1] - self.nextNodePos[1]
        
        if dx == 0 and dy == 0:
            # if at the same node, do nothing.
            return
        
        absx = abs(dx)
        absy = abs(dy)
        
        curAngle = self.getH()
        
        if self.finishedTurning == True :
            if absx == 0 and absy != 0 : 
                self.nextAngle = math.acos(dy/absy)
                self.nextAngle = math.degrees(self.nextAngle)
                if dx != 0:
                    self.nextAngle += 180
            elif absy == 0 and absx != 0 : 
                self.nextAngle = math.asin(dx/absx)
                self.nextAngle = math.degrees(self.nextAngle)
                if dx != 0:
                    self.nextAngle += 180
            else:
                self.nextAngle = math.atan(dx/dy)
                self.nextAngle = math.degrees(self.nextAngle)
                self.nextAngle % 90
                if dy > 0 and dx > 0:
                    pass
                elif dy < 0 and dx < 0:
                    self.nextAngle = self.nextAngle + 180
                elif dy < 0 and dx > 0:
                    self.nextAngle = self.nextAngle + 180 - 2 * self.nextAngle
                elif dy > 0 and dx < 0:
                    self.nextAngle = self.nextAngle + 360 - 2 * self.nextAngle
                    
                #self.nextAngle = self.nextAngle - 90
            #print "(1) DX: " + str(dx) + " DY: " + str(dy) + " Angle: " + str(self.nextAngle) + " CurAngle: " + str(curAngle)
            
            self.finishedTurning = False    
            self.nextAngle = self.nextAngle % 360
            #print "(1) DX: " + str(dx) + " DY: " + str(dy) + " Angle: " + str(self.nextAngle) + " CurAngle: " + str(curAngle)
        # most the panda should ever have to turn is 180 degrees.
        angleDiff = abs( curAngle - self.nextAngle )
        if angleDiff > 180:
            if curAngle == 270 and self.nextAngle == 0:
                self.nextAngle = 360
            #print " Angle Diff: " + str(angleDiff)
            else:
                angleDiff -= 180
                angleDiff *= -1
                self.nextAngle = angleDiff
            #print " Angle Diff: " + str(angleDiff)
        
        
        
        #print "(2) Abs X: " + str(absx) + " Abs Y: " + str(absy) + " Angle: " + str(self.nextAngle) + " CurAngle: " + str(curAngle)
        if abs(curAngle - self.nextAngle) < ANGLE_LEEWAY:
            self.setH(self.nextAngle)
            #print "(1): " + str(self.getH())
            while self.getH() < 0:
                self.setH(self.getH() + 360)
            #print "(2): " + str(self.getH()
            if self.getH() == 360:
                self.setH(0)
            self.phase = MOVING
            self.finishedTurning = True
            #print "inside leeway"
        else:
            if curAngle < self.nextAngle:
                self.setH(curAngle + elapsed * self.turnSpeed)
            elif curAngle > self.nextAngle:
                self.setH(curAngle + elapsed * self.turnSpeed * - 1)
        self.prevtime = task.time
        
    def move( self, map, task ):
        
        #check if enemy is at node, if so, then change lastNode and nextNode
        #print "X: " + str(int(self.getX())) + " vs "  + str(self.nextNodePos[0])
        #print "Y: " + str(int(self.getY())) + " vs "  + str(self.nextNodePos[1])
        #print "Index: " + str(self.curNodeIndex)
        #print self.lastNodePos
        #print self.nextNodePos
        #print "Index: " + str(self.curNodeIndex)
        if self.phase == TURNING:
            self.stop()
            self.pose("drive", 4)
            self.turn( task )
        elif self.phase == MOVING:
            self.loop("drive")
            if abs(self.getX() - self.nextNodePos[0] ) < LEEWAY and abs(self.getY() - self.nextNodePos[1] ) < LEEWAY :
                self.setX(self.nextNodePos[0])
                self.setY(self.nextNodePos[1])
                self.curNodeIndex = self.curNodeIndex + 1
                if self.curNodeIndex == len(self.nodePath) - 1:
                    self.nextNodePos = map.nodeList[self.nodePath[0]].getPos()
                elif self.curNodeIndex == len(self.nodePath):
                    self.curNodeIndex = 0 
                    self.nextNodePos = map.nodeList[self.nodePath[self.curNodeIndex+1]].getPos()
                else:
                    self.nextNodePos = map.nodeList[self.nodePath[self.curNodeIndex+1]].getPos()
                self.lastNodePos = map.nodeList[self.nodePath[self.curNodeIndex]].getPos()    
                self.phase = TURNING
            elapsed = task.time -self.prevtime
            dist = self.speed * elapsed  
            
            dx = self.getX() - self.nextNodePos[0]
            dy = self.getY() - self.nextNodePos[1]
            
            #print "Dx: " + str(dx)
            #print "Dy: " + str(dy)
            
            xdir = 0
            ydir = 0
            
            #if ( self.getH() % 45 ) != 0:
                #print str(self.firstNode) + ": H: " + str(self.getH())
            
            if dx > 0:
                xdir = -1
            elif dx < 0:
                xdir = 1
                
            if dy > 0 :
                ydir = -1
            elif dy < 0:
                ydir = 1
                
            dx = xdir * dist
            dy = ydir * dist
            
            self.setPos(self.getX() + dx, self.getY() + dy, 0)
            self.prevtime = task.time
        elif self.phase == STOPPED:
            if task.time - self.prevtime > STUN_LENGTH:
                self.phase = self.prevPhase
                self.prevtime = task.time
                self.headlight1.setColor(VBase4(75, 75, 75, 75))
        return Task.cont
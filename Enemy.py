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


MOVING = 0
TURNING = 1


TURNTIME = 5

class Enemy(vehicle.Vehicle):
    def __init__(self, map, nodePath, world, x, y, z ):
        vehicle.Vehicle.__init__(self, "models/panda-model", "panda-walk4", world)
        self.setPos(x,y,z)
        self.nodePath = nodePath
        
        self.curNodeIndex = 0 
        self.speed = 4.0
        
        self.turnTime = TURNTIME
        self.turnSpeed = 40.0
        
        self.phase = MOVING
        
        self.lastNodePos = map.nodeList[nodePath[self.curNodeIndex]].getPos()
        self.nextNodePos = map.nodeList[nodePath[self.curNodeIndex+1]].getPos()
        
        self.finishedTurning = True
        
    def turn( self, task ):
        elapsed = task.time - self.prevtime
        dx = self.lastNodePos[0] - self.nextNodePos[0]
        dy = self.lastNodePos[1] - self.nextNodePos[1]
        
        absx = abs(dx)
        absy = abs(dy)
        
        curAngle = self.getH()
        
        if self.finishedTurning == True :
            if absx == 0 and absy != 0 : 
                self.nextAngle = math.acos(dy/absy)
            elif absy == 0 and absx != 0 : 
                self.nextAngle = math.asin(dx/absx)
            else:
                self.nextAngle = math.atan(dx/dy)
            self.nextAngle = math.degrees(self.nextAngle)
            if dx != 0:
                self.nextAngle += 180
            self.finishedTurning = False    
            
        #print "(1) DX: " + str(dx) + " DY: " + str(dy) + " Angle: " + str(self.nextAngle) + " CurAngle: " + str(curAngle)
        
        # most the panda should ever have to turn is 180 degrees.
        angleDiff = abs( curAngle - self.nextAngle )
        if angleDiff > 180:
            #print " Angle Diff: " + str(angleDiff)
            angleDiff -= 180
            angleDiff *= -1
            self.nextAngle = angleDiff
        
        
        
        #print "(2) Abs X: " + str(absx) + " Abs Y: " + str(absy) + " Angle: " + str(self.nextAngle) + " CurAngle: " + str(curAngle)
        if abs(curAngle - self.nextAngle) < ANGLE_LEEWAY:
            self.setH(self.nextAngle)
            while self.getH() < 0:
                self.setH(self.getH() + 360)
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
            self.turn( task )
        elif self.phase == MOVING:
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
        return Task.cont
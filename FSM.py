from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from pandac.PandaModules import TextNode
from direct.fsm.FSM import FSM
from direct.gui.OnscreenImage import OnscreenImage
from direct.stdpy.threading import Timer
from direct.task import Task
import menus
import sys
from world import World

class MenuFSM(FSM):

    def __init__(self):
        FSM.__init__(self, 'MenuFSM')
        self.frame = DirectFrame(frameColor = (255,255,255,1),
                                 frameSize = (-1.5,1.5,-1,1),
                                 pos = (0,0,0))

    def enterMenu(self):
        self.mainBackground = OnscreenImage(image = 'images/titleScreen.png', scale = (1.3333333,1, 1))
        self.createMenu(menus.mainMenu, startPos = (-0.7,-13,0), parent = self.mainBackground, increment = 0.2)
        # for button in self.buttons:
        # 	button.reparentTo(self.mainBackground)
        
    def exitMenu(self):
        self.mainBackground.destroy()

    def enterGame(self):
        self.loading = OnscreenImage(image = 'images/loading.png', scale = (1.3333333,0, 1))
        taskMgr.doMethodLater(1, self.startGame, 'tickTask')

        
    def startGame(self, THING):
        print "lol"
        self.world = World()
        self.world.accept("escape", self.request, ['Menu'])
        print "abc"
        self.loading.destroy()
        self.frame.destroy()
        
    def exitGame(self):
        sys.exit()

    def enterInstructions(self):
        imageObject = OnscreenImage(image = 'myImage.jpg', pos = (-0.5, 0, 0.02))

    def exitInstructions(self):
        self.credits = OnscreenImage(image = 'images/credits.png', pos = (-0.5, 0, 0.02))

    def enterCredits(self):
        self.credits = OnscreenImage(image = 'images/credits.png', scale = (1.3333333,0, 1))
        self.credits.accept('escape', self.request, ['Menu'])

    def exitCredits(self):
        self.credits.destroy()

    def createMenu(self, menu, startPos=(0,-13,.9), parent = None, increment = 0.3):
        self.buttons = list()

        if parent is None:
        	parent = self.frame

    	font = loader.loadFont('fonts/beneg.ttf')
    	scale = 0.10

        x = startPos[0]
        y = startPos[1]
        z = startPos[2]

        for v in menu.values():
            
            if 'args' in v:
                temp = DirectButton(text = v['text'],
					                scale=scale,
					                command=v['function'],
					                extraArgs=v.get('args'),
					                pos=(x,y,z),
					                parent = parent,
					                text_font = font,
					                text_fg = (255,255,255,1),
					                frameColor = (0,0,0,0)
					                )
            else:
                temp = DirectButton(text = v['text'],
                					scale=scale,
                					command=v['function'],
                					pos=(x,y,z),
                					parent = parent,
                					text_font = font,
                					text_fg = (255,255,255,1),
                					frameColor = (0,0,0,0))
            self.buttons.append(temp)
            z = z - increment
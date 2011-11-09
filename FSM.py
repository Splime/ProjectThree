from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from pandac.PandaModules import TextNode
from direct.fsm.FSM import FSM
from direct.gui.OnscreenImage import OnscreenImage
import menus

class MenuFSM(FSM):

	def __init__(self):
		FSM.__init__(self, 'MenuFSM')
		self.frame = DirectFrame(frameColor = (255,255,255,1),
								 frameSize = (-1.5,1.5,-1,1),
								 pos = (0,0,0))

	def enterMenu(self):
		self.createMenu(menus.mainMenu)
	def exitMenu(self):
		for i in self.buttons:
			i.destroy()

	def enterPlay(self):
		pass
	def exitPlay(self):
		pass

	def enterInstructions(self):
		imageObject = OnscreenImage(image = 'myImage.jpg', pos = (-0.5, 0, 0.02))

	def exitInstructions(self):
		self.credits = OnscreenImage(image = 'images/credits.png', pos = (-0.5, 0, 0.02))

	def enterCredits(self):
		self.credits = OnscreenImage(image = 'images/credits.png', scale = (1.3333333,0, 1))
		self.credits.accept('escape', self.request, ['Menu'])
	def exitCredits(self):
		self.credits.destroy()

	def createMenu(self, menu):
		self.buttons = list()

		x = 0
		y = -13
		z = .9

		for v in menu.values():
			
			if 'args' in v:
				temp = DirectButton(text = v['text'], scale=.05, command=v['function'], extraArgs=v.get('args'), pos=(x,y,z), parent = self.frame)
			else:
				temp = DirectButton(text = v['text'], scale=.05, command=v['function'], pos=(x,y,z), parent = self.frame)
			self.buttons.append(temp)
			z = z - 0.3
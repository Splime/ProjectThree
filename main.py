from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "fullscreen 1") # Set to 1 for fullscreen
loadPrcFileData("", "window-title Vampire Car")
loadPrcFileData("", "win-size 1024 768")
loadPrcFileData("", "win-origin 30 30")
import direct.directbase.DirectStart #starts player
from pandac.PandaModules import * #basic Panda modules
import FSM
import menus

# winprops = WindowProperties()
stateMachine = FSM.MenuFSM()
menus.createMenus(stateMachine)
stateMachine.request('Menu')
base.enableMusic(True)
theMusic = base.loader.loadSfx("sound/385977_Carnival.mp3")
theMusic.setLoop(True)
theMusic.play()
run()
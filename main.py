import direct.directbase.DirectStart #starts player
from pandac.PandaModules import * #basic Panda modules
import FSM
import menus

# winprops = WindowProperties()
stateMachine = FSM.MenuFSM()
menus.createMenus(stateMachine)
stateMachine.request('Menu')
run()
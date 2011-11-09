import direct.directbase.DirectStart #starts player
import FSM
import menus

stateMachine = FSM.MenuFSM()
menus.createMenus(stateMachine)
stateMachine.request('Menu')
run()
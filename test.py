import direct.directbase.DirectStart
# from FSM import MenuFSM
import FSM
import menus

stateMachine = FSM.MenuFSM()
menus.createMenus(stateMachine)
stateMachine.request('Menu')
run()
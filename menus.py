import sys

def doNothing():
    pass

mainMenu = {}
optionsMenu = {}

def createMenus(stateMachine):
    global mainMenu
    mainMenu = {
        0: {
            'text':'New Game',
            'function': stateMachine.request,
            'args' : ['Game']
        },
        1: {
            'text':'Instructions',
            'function': stateMachine.request,
            'args' : ['Instructions']
        },
        2: {
            'text':'Credits',
            'function': stateMachine.request,
            'args' : ['Credits']
        },
        3: {
            'text':'Exit',
            'function': sys.exit
        }
    }

    global optionsMenu
    optionsMenu = {
        0: {
            'text':'Option 1',
            'function': doNothing
        },
        1: {
            'text':'Option 2',
            'function': doNothing
        },
        2: {
            'text':'Credits',
            'function': stateMachine.request,
            'args': ['Menu']
        }
    }
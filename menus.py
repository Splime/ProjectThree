def doNothing():
	pass

mainMenu = {}
optionsMenu = {}

def createMenus(stateMachine):
	global mainMenu
	mainMenu = {
		0: {
			'text':'Play Game',
			'function': doNothing
		},
		1: {
			'text':'Options',
			'function': stateMachine.request,
			'args' : ['Options']
		},
		2: {
			'text':'Credits',
			'function': doNothing
		},
		3: {
			'text':'Exit',
			'function': doNothing
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
#Author-Jerome Briot
#Description-

import adsk.core, adsk.fusion, traceback  # pylint: disable=import-error
import platform, subprocess
import tempfile, json
import os, re
from copy import deepcopy
thisAddinName = 'OpenFolders'
thisAddinTitle = 'Open Folders'
thisAddinVersion = '0.4.0'
thisAddinAuthor = 'Jerome Briot'
thisAddinContact = 'jbtechlab@gmail.com'

handlers = []
iswindows = platform.system() == 'Windows'
app = adsk.core.Application.cast(adsk.core.Application.get())
ui  = app.userInterface

# https://forums.autodesk.com/t5/fusion-360-api-and-scripts/api-bug-cannot-click-menu-items-in-nested-dropdown/m-p/9669144#M10876
nestedMenuBugFixed = False
showUndocumentedFolders = True
thisFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)))
appdataPath = None

emptyControls = {
			'titles': [],
			'ids': [],
			'parentsIds': [],
			'types': [],
			'paths': [],
			'separators': [],
			'icons': [] }
controls = deepcopy(emptyControls)
undocumentedControls = deepcopy(emptyControls)


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

def getUserDataPath():
	dataPath = CheckDir(os.path.join(appdataPath, thisAddinName + 'ForFusion360'))
	return CheckDir(os.path.join(dataPath, app.userId))


def getDefaultControls():
	global controls, emptyControls, undocumentedControls, appdataPath
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	if iswindows:
		userPath = os.getenv('USERPROFILE')
		desktopPath = os.path.join(userPath, 'Desktop')
		tempDataPath = os.path.join(os.getenv('TMP'))

		appdataPath = os.path.join(os.getenv('APPDATA'))
		localAppdataPath = os.path.join(os.getenv('LOCALAPPDATA'))
		
		autodeskLocal = os.path.join(localAppdataPath, 'Autodesk')
		autodeskRoaming = os.path.join(appdataPath, 'Autodesk')

		directory = os.path.join(localAppdataPath, 'Autodesk', 'webdeploy', 'production')
		fusion360Install = max([os.path.join(directory,d) for d in os.listdir(directory)], key=os.path.getctime)

		fusion360ApiCpp = os.path.join(fusion360Install, 'CPP')
		fusion360ApiPython = os.path.join(fusion360Install, 'Api', 'Python')
		fusion360Python = os.path.join(fusion360Install, 'Python')

		userDataPath = getUserDataPath()
	else:
		userPath = os.path.expanduser('~')
		desktopPath = os.path.join(userPath, 'Desktop')
		tempDataPath = os.path.join("/tmp" if platform.system() == "Darwin" else tempfile.gettempdir())

		appdataPath = os.path.join(userPath, 'Library', 'Application Support')

		autodeskPath = os.path.join(appdataPath, 'Autodesk')
		
		fusionAppPath = os.path.realpath(os.path.join(autodeskPath, 'webdeploy', 'production', 'Autodesk Fusion 360.app'))
		fusion360Install = os.path.join(fusionAppPath, 'Contents')

		fusion360ApiCpp = os.path.join(fusion360Install, 'Libraries', 'Neutron', 'CPP')
		fusion360ApiPython = os.path.join(fusion360Install, 'Api', 'Python')
		fusion360Python = os.path.join(fusion360Install, 'Frameworks', 'Python.framework', 'Versions')

		userDataPath = getUserDataPath()
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	rootGroups = {
	'Fusion360':[{'Icon': 'fusion360'},
		{'Title': 'Install', 			'ItemID': 'FusionInstall', 		'ParentID': 'root',			'Type': 'command',		'Path': fusion360Install },
		{'Title': 'API', 				'ItemID': 'FusionApi', 			'ParentID': 'root',			'Type': 'dropdown',		'Path': None },
		{'Title': 'C++', 				'ItemID': 'FusionApiCpp', 		'ParentID': 'FusionApi',	'Type': 'command',		'Path': fusion360ApiCpp },
		{'Title': 'Python', 			'ItemID': 'FusionApiPython', 	'ParentID': 'FusionApi',	'Type': 'command',		'Path': fusion360ApiPython },
		{'Title': 'Python', 			'ItemID': 'FusionPython', 		'ParentID': 'root',			'Type': 'command',		'Path': fusion360Python }],
	'Autodesk':[{'Icon': 'autodesk'},
		{'Title': 'Autodesk', 			'ItemID': 'Autodesk', 			'ParentID': 'root',			'Type': 'dropdown',		'Path': None },
		{'Title': 'Autodesk (Local)', 	'ItemID': 'AutodeskLocal', 		'ParentID': 'Autodesk',		'Type': 'command',		'Path': autodeskLocal },
		{'Title': 'Autodesk (Roaming)', 'ItemID': 'AutodeskRoaming', 	'ParentID': 'Autodesk',		'Type': 'command',		'Path': autodeskRoaming }]
		if iswindows else [{'Icon': 'autodesk'},
		{'Title': 'Autodesk', 			'ItemID': 'Autodesk', 			'ParentID': 'root',			'Type': 'command',		'Path': autodeskPath }],
	'System':[{'Icon': 'system'},
		{'Title': 'Desktop', 			'ItemID': 'Desktop', 			'ParentID': 'root',			'Type': 'command',		'Path': desktopPath },
		{'Title': 'Temp Data', 			'ItemID': 'TempFiles', 			'ParentID': 'root',			'Type': 'command',		'Path': tempDataPath },
		{'Title': 'Appdata', 			'ItemID': 'Appdata', 			'ParentID': 'root',			'Type': 'dropdown',		'Path': None },
		{'Title': 'Appdata (Local)', 	'ItemID': 'AppdataLocal', 		'ParentID': 'Appdata',		'Type': 'command',		'Path': localAppdataPath },
		{'Title': 'Appdata (Roaming)', 	'ItemID': 'AppdataRoaming', 	'ParentID': 'Appdata',		'Type': 'command',		'Path': appdataPath }]
		if iswindows else [{'Icon': 'system'},
		{'Title': 'Desktop', 			'ItemID': 'Desktop', 			'ParentID': 'root',			'Type': 'command',		'Path': desktopPath },
		{'Title': 'Appdata', 			'ItemID': 'Appdata', 			'ParentID': 'root',			'Type': 'command',		'Path': tempDataPath },
		{'Title': 'Temp Data', 			'ItemID': 'TempFiles', 			'ParentID': 'root',			'Type': 'command',		'Path': appdataPath }],
	'Settings':[{	'Icon': ''},
		{'Title': 'Settings', 			'ItemID': 'Settings', 			'ParentID': 'root',			'Type': 'command',		'Path': userDataPath }]}

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	controls = deepcopy(emptyControls)
	for groupList in rootGroups.values():
		icon = groupList[0]['Icon']
		if icon == 'system': icon = 'windows' if iswindows else 'macos'
		lastWholeID = len(controls['separators']) 
		for item in range(1,len(groupList)):
			controls['titles'].append(groupList[item]['Title'])
			controls['ids'].append(groupList[item]['ItemID'])
			controls['parentsIds'].append(groupList[item]['ParentID'])
			controls['types'].append(groupList[item]['Type'])
			controls['paths'].append(groupList[item]['Path'])
			controls['icons'].append(icon)
			controls['separators'].append(False)
			if groupList[item]['ParentID'] == 'root': lastWholeID = len(controls['separators']) - 1
		controls['separators'][lastWholeID] = True

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	getUndocumentedControls()
	getCustomControls()

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
	# ui.messageBox(str(controls))


		# if not nestedMenuBugFixed:
		#     controls['separators'][1] = True

def getUndocumentedControls():
	global undocumentedControls
	if not nestedMenuBugFixed: undocumentedControls = deepcopy(emptyControls)
	else: idx = 4

	if nestedMenuBugFixed:
		controls['titles'].insert(idx, 'Undocumented')
		controls['ids'].insert(idx, 'Undocumented')
		controls['parentsIds'].insert(idx, 'root')
		controls['types'].insert(idx, 'dropdown')
		controls['paths'].insert(idx, None)
		controls['separators'].insert(idx, True)
		controls['icons'].insert(idx, 'fusion360')

	pathsDict = json.loads(app.executeTextCommand('Paths.Get'))
	for key in pathsDict.keys():
		if key != 'isInstalledBuild':
			pn = ' '.join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', key[0].upper() + key[1:]))

			if pathsDict[key].startswith('Auto-save location is '):
				pp = pathsDict[key].replace('Auto-save location is ', '')
			else: pp = pathsDict[key]
			if key == 'AppLogFilePath': pp = os.path.dirname(pp)
			if not pp.endswith('/'): pp += '/'
			pt = pn if os.path.exists(pp) else '~' + pn + ' (Broken)'

			if nestedMenuBugFixed:
				idx += 1
				controls['titles'].insert(idx, pt)
				controls['ids'].insert(idx, pn.replace(' ', ''))
				controls['parentsIds'].insert(idx, 'Undocumented')
				controls['types'].insert(idx, 'command')
				controls['paths'].insert(idx, pp)
				controls['separators'].insert(idx, False)
				controls['icons'].insert(idx, 'fusion360')
			else:
				undocumentedControls['titles'].append(pt)
				undocumentedControls['ids'].append(pn.replace(' ', ''))
				undocumentedControls['parentsIds'].append('root')
				undocumentedControls['types'].append('command')
				undocumentedControls['paths'].append(pp)
				undocumentedControls['separators'].append(False)
				undocumentedControls['icons'].append('fusion360')


def getCustomControls():
	global controls
	customPathFile = os.path.join(getUserDataPath(), 'customPaths.json')
	if not os.path.exists(customPathFile): createJsonFiles(customPathFile); return

	with open(customPathFile, 'r') as file: customControls = json.load(file)
	controls['titles'] =	 controls['titles'][0:-1] + customControls['titles'] + [controls['titles'][-1]]
	controls['ids'] = 		controls['ids'][0:-1] + customControls['ids'] + [controls['ids'][-1]]
	controls['parentsIds'] = controls['parentsIds'][0:-1] + customControls['parentsIds'] + [controls['parentsIds'][-1]]
	controls['types'] = 	controls['types'][0:-1] + customControls['types'] + [controls['types'][-1]]
	controls['paths'] = 	controls['paths'][0:-1] + customControls['paths'] + [controls['paths'][-1]]
	controls['separators'] = controls['separators'][0:-1] + customControls['separators'] + [controls['separators'][-1]]
	controls['icons'] = 	controls['icons'][0:-1] + customControls['icons'] + [controls['icons'][-1]]




#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
def checkResources(controlDict):
	for i in range(0, len(controlDict['icons'])):
		if controlDict['icons'][i] != '':
			if os.path.exists(os.path.join(thisFilePath, 'resources', controlDict['icons'][i])):  
					controlDict['icons'][i] = 'resources/' + controlDict['icons'][i]
			else: 	controlDict['icons'][i] = ''

class commandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
	def __init__(self): super().__init__()
	def notify(self, args):
		try:
			global controls, undocumentedControls
			senderId = args.firingEvent.sender.id[len(thisAddinName):]
			if senderId in controls['ids']: controlDict = controls
			elif senderId in undocumentedControls['ids']: controlDict = undocumentedControls
			else: BetterErrorCast('Control not in lists'); return

			idx = controlDict['ids'].index(senderId)
			if controlDict['paths'][idx]: path = os.path.realpath(controlDict['paths'][idx])

			path = CheckDir(path, False)
			if iswindows: os.startfile(path)
			else: subprocess.check_call(["open", "--", path])
		except: BetterErrorCast()


def run(context):
	try:
		global controls, undocumentedControls, emptyControls
		def createControls(controlDict, dropdownID):
			checkResources(controlDict)
			for i in range(0, len(controlDict['titles'])):
				if controlDict['types'][i] == 'command':
					
					button = ui.commandDefinitions.itemById(str(MakeID(controlDict['ids'][i])))
					if button: 
						ui.messageBox(str(button.id + ": Already defined"   ))
						ui.messageBox(str("Is this button Native to F360?: " + str(button.isNative)))
						if not button.isNative: button.deleteMe()
					
					button = ui.commandDefinitions.addButtonDefinition(MakeID(controlDict['ids'][i]), controlDict['titles'][i], controlDict['paths'][i], controlDict['icons'][i])
					button.commandCreated.add(commandCreated)
					handlers.append(commandCreated)


					dropdown:adsk.core.DropDownControl = solidScripts.controls.itemById(dropdownID)
					if controlDict['parentsIds'][i] != 'root':	
						dropdown = dropdown.controls.itemById(MakeID(controlDict['parentsIds'][i]))
					dropdown.controls.addCommand(button)
				else:
					dropdown = solidScripts.controls.itemById(dropdownID)
					dropdown.controls.addDropDown(controlDict['titles'][i], controlDict['icons'][i], MakeID(controlDict['ids'][i]), '', False)
				if controlDict['separators'][i]: dropdown.controls.addSeparator(MakeID(controlDict['ids'][i] + 'separator'), '')


		getDefaultControls()
		commandCreated = commandCreatedEventHandler()
		solidScripts = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
		solidScripts.controls.addSeparator(MakeID('separatorTop'), '')
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		solidScripts.controls.addDropDown(thisAddinTitle, '', MakeID('root' + 'Dropdown'), '', False)
		createControls(controls, MakeID('root' + 'Dropdown'))
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		if not nestedMenuBugFixed and showUndocumentedFolders:
			solidScripts.controls.addDropDown(thisAddinTitle + ' (undocumented)', '', MakeID('root'+'Dropdown'+'Undoc'), '', False)
			createControls(undocumentedControls, MakeID('root'+'Dropdown'+'Undoc'))
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		solidScripts.controls.addSeparator(MakeID('separatorBottom'), '')
		if context['IsApplicationStartup'] is False: ui.messageBox("The '{}' command has been added\nto the ADD-INS panel of the DESIGN workspace.".format(thisAddinTitle), '{} v{}'.format(thisAddinTitle, thisAddinVersion))
	except: cleanUI(errorCleanup=True)

def stop(context): cleanUI()


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

def ErrorCast(): 
	if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()), '{} v{}'.format(thisAddinTitle, thisAddinVersion))

def BetterErrorCast(args:str = 'Failed:\n{}'): 
	if ui: ui.messageBox((args + '\n{}').format(traceback.format_exc()), '{} v{}'.format(thisAddinTitle, thisAddinVersion), adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)

def CheckDir(dataPath, makeDir = True):
	if dataPath and os.path.exists(dataPath): return dataPath
	if makeDir:
		os.mkdir(dataPath)
		return dataPath
	else: BetterErrorCast('Path not found: ' + dataPath)

def MakeID(idVal:str): return thisAddinName + idVal

def createJsonFiles(customPathFile): 
	with open(customPathFile, 'w') as f: json.dump(deepcopy(emptyControls), f, indent=2)

def checkDelete(item): 
	if not item: return True
	if isinstance(item, adsk.core.CommandControl): item.isPromoted = False
	return item.deleteMe()


def cleanUI(errorCleanup = False):
	try:
		global controls, undocumentedControls
		def loopDropdown(controlDict, ctrlID:str):
			dropdownCntr:adsk.core.DropDownControl = solidScriptsControls.itemById(ctrlID)
			for i in range(0, len(controlDict['titles'])):
				checkDelete(ui.commandDefinitions.itemById(MakeID(controlDict['ids'][i])))
				if dropdownCntr:
					checkDelete(dropdownCntr.controls.itemById(MakeID(controlDict['ids'][i])))
					if controlDict['separators'][i]: 
						checkDelete(dropdownCntr.controls.itemById(MakeID(controlDict['ids'][i] + 'separator')))
			checkDelete(dropdownCntr)

		solidScriptsControls = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel').controls
		checkDelete(solidScriptsControls.itemById(MakeID('separatorTop')))
		loopDropdown(controls, MakeID('root' + 'Dropdown'))
		if not nestedMenuBugFixed: loopDropdown(undocumentedControls, MakeID('root'+'Dropdown'+'Undoc'))
		checkDelete(solidScriptsControls.itemById(MakeID('separatorBottom')))
	except: ErrorCast()
	if errorCleanup: ErrorCast()

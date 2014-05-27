# Copyright Kumaran S/O Murugun 2014
# License - Apache 2.0

from platform import system
from os import path, walk
from subprocess import check_call
import maya.cmds as cmds
import maya.mel as mel


SYSTEM = system()
IS_OSX = SYSTEM == 'Darwin'
IS_WINDOWS = SYSTEM == 'Windows'


def getDefaultProject():
    return cmds.internalVar(userWorkspaceDir=True)

def getCurrentProject():
    return cmds.workspace(q=True, directory=True)

def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(path.sep)
    # assert path.isdir(some_dir)
    num_sep = some_dir.count(path.sep)
    for root, dirs, files in walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def getFolders(location=None, subfolders=1):
    if location is None:
        location = getCurrentProject()
        if not path.exists(location):
            location = getDefaultProject()
    return [i[0] for i in walklevel(location, subfolders)]

def getFiles(location=None, subfolders=2):
    if location is None:
        location = getCurrentProject()
        if not path.exists(location):
            location = getDefaultProject()
    files = [i for i in walklevel(location, subfolders) if i[2] != []]
    tmp = []
    for x in files:
        for afile in x[2]:
            tmp.append(path.join(x[0], afile))
    return tmp

def openLocation(location=None):
    if location is None:
        location = getCurrentProject()
        if not path.exists(location):
            location = getDefaultProject()
    if IS_OSX and path.exists(location):
        return check_call(['open', '--', location])
    elif IS_WINDOWS and path.exists(location):
        return check_call(['explorer', location.replace('/', '\\')])

def print_message(message):
    mel.eval("print \"{0}\\n\";".format(message))

def UI():
    #check to see if window exists
    if cmds.window("mkProjects", exists=True):
        cmds.deleteUI("mkProjects")

    #main window
    window = cmds.window("mkProjects", title="Project Quick Load", width=400, 
                        height=300, mnb=False, mxb=False, sizeable=False)

    #main layout
    mainLayout = cmds.columnLayout(width=400, height=300)

    #banner image
    imagePath = path.join(cmds.internalVar(upd=True), 'icons', 'mkProjects.jpg')
    #load image
    cmds.image(width=400, height=100, image=imagePath)

    cmds.separator(height=15)
    cmds.textField('location', width=400, editable=False, 
        text=getDefaultProject())

    #create projects option menu
    projectsOptionMenu = cmds.optionMenu("projectsOptionMenu", width=400, 
        label="Choose a project: ", cc=populateScenes)

    #populate projects with maya default project location
    populateProjects()

    cmds.separator(height=15)
    rowLayout = cmds.rowLayout(nc=2)

    #List Control
    scenesList = cmds.textScrollList("scenesList", 
        allowMultiSelection=False, width=300, dcc=loadFile)
    populateScenes()

    colLayout = cmds.columnLayout()
    cmds.button(label="Set Location", width=95, height=30, c=setLocation)
    cmds.separator(height=5)
    cmds.button(label="Create Project", width=95, height=30, 
        c=cmds.ProjectWindow)
    cmds.separator(height=5)
    cmds.button(label="Open Project", width=95, height=30, c=openProject)
    cmds.separator(height=5)
    cmds.button(label="Open Scenes", width=95, height=30, c=openScenes)
    cmds.separator(height=5)
    cmds.button(label="Open Textures", width=95, height=30, c=openTextures)
    cmds.separator(height=5)
    cmds.button(label="Open Renders", width=95, height=30, c=openRenders)

    #open scene button
    cmds.separator(height=15, parent=mainLayout)
    cmds.button(label="Load File", width=400, height=50, parent=mainLayout, 
        c=loadFile)

    #show window
    cmds.showWindow(window)

def populateProjects(patch=False):
    location = cmds.textField('location', q=True, text=True)
    #Get the projects from Maya Default Projects Location and populate
    for project in getFolders(location)[1::]:
        #Add project to the projectsOptionMenu
        if IS_WINDOWS:
            if not '\\' in project:
                cmds.menuItem(label=project.rpartition('/')[2], 
                parent="projectsOptionMenu")
            elif patch is True:
                x = project.replace('\\', '/')
                cmds.menuItem(label=x.rpartition('/')[2], 
                parent="projectsOptionMenu")
        else:
            cmds.menuItem(label=project.rpartition(path.sep)[2], 
                parent="projectsOptionMenu")

def populateScenes(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedmenu = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #Remove all entries inside the List Box
    cmds.textScrollList("scenesList", e=True, ra=True)

    #FullPath to the selected project's scene folder
    projectScenePath = path.join(location, selectedmenu, 'scenes')

    #Get the maya binary files
    files = getFiles(projectScenePath)
    
    for i in files:
        afile = i.replace(projectScenePath+path.sep, '')
        if afile.endswith('.mb') or afile.endswith('.ma'):
            #append files to the List Box
            cmds.textScrollList("scenesList", e=True, a=afile)

def loadFile(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedProject = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #Get the selected scene
    selectedScene = cmds.textScrollList("scenesList", q=True, si=True)[0]
    
    #Recreate the full path to the file
    filepath = path.join(location, selectedProject, 'scenes', 
        selectedScene)

    #Selected Project Path
    selectedProjectPath = path.join(location, selectedProject)

    if IS_WINDOWS:
        selectedProjectPath = selectedProjectPath.replace('\\', '/')
        filepath = filepath.replace('\\', '/')
    
    #form the message
    message = 'Opening File... {0}'.format(filepath)
    
    #print the mesage using mel so that maya outputs in bar
    print_message(message)

    #Set the project workspace to selected project
    mel.eval("setProject \"{0}\";".format(selectedProjectPath))

    #open the file
    cmds.file(filepath, open=True, force=True, prompt=False)

def openProject(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedmenu = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #FullPath to the selected project's folder
    projectPath = path.join(location, selectedmenu)

    #open the location
    openLocation(projectPath)

def openScenes(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedmenu = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #FullPath to the selected project's scene folder
    projectScenePath = path.join(location, selectedmenu, 'scenes')

    #open the location
    openLocation(projectScenePath)

def openTextures(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedmenu = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #FullPath to the selected project's sourceimages folder
    projectSourceImagesPath = path.join(location, selectedmenu, 
        'sourceimages')

    #open the location
    openLocation(projectSourceImagesPath)

def openRenders(*args):
    location = cmds.textField('location', q=True, text=True)
    #Get the selected project
    selectedmenu = cmds.optionMenu("projectsOptionMenu", q=True, v=True)
    
    #FullPath to the selected project's images folder
    projectImagesPath = path.join(location, selectedmenu, 'images')

    #open the location
    openLocation(projectImagesPath)

def setLocation(*args):
    #Prompt the user to select a folder
    newLocation = cmds.fileDialog2(dialogStyle=2, fileMode=3, 
        okCaption='Set Location')

    #Set the selected folder to the textfield
    cmds.textField('location', e=True, text=str(newLocation[0]))

    # Delete all projects in option menu
    menuItems = cmds.optionMenu("projectsOptionMenu", q=True, ill=True)
    if menuItems != None and menuItems != []:
        cmds.deleteUI(menuItems)
    
    #Re-populate with new location projects
    populateProjects(patch=True)

    #Re-populate with new scenes
    populateScenes()
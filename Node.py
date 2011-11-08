import math

class Node():
    def __init__(self, x , y , z):
        self.x = x
        self.y = y
        self.z = z
        
        # list of adjacent nodes 
        self.adjacentNodes = []
        self.adjacentNodesDistances = []
    def getPos(self):
        return self.x, self.y, self.z
    def getAdjacentNodes(self):
        return self.adjacentNodes
    def getRandomAdjacentNode(self):
        pass 
    def setAdjacentNode(self, num, dist ):
        self.adjacentNodes.append( num )
        self.adjacentNodesDistances.append( dist ) 
        
class NodeMap():
    def __init__(self, filename):
        self.nodeList = []
        self.populateNodeList( filename )
        
    def populateNodeList(self, filename):
        file = open('levels/' + filename, 'r')
        
        # initial population of nodeList
        line = file.readline().rstrip()
        while line != "#" :
            nums = line.split(',')
            self.nodeList.append( Node( int(nums[1]), int(nums[2]), int(nums[3] )))
            line = file.readline().rstrip()
        line = file.readline().rstrip()
        while line != "" :
            nums = line.split(',')
            for num in nums :
                currNode = int(nums[0])
                adjNode = int(num)
                if currNode != adjNode:
                    dist = math.sqrt(     math.pow((self.nodeList[currNode].x - self.nodeList[adjNode].x ), 2) 
                                        + math.pow((self.nodeList[currNode].y - self.nodeList[adjNode].y ), 2)
                                        + math.pow((self.nodeList[currNode].z - self.nodeList[adjNode].z ), 2))
                    self.nodeList[currNode].setAdjacentNode(adjNode, dist )
            line = file.readline().rstrip()
        
    def getNode(self, index):
        return nodeList[index]

"""
map = NodeMap("nodes.txt")
i = 0

for node in map.nodeList:
    print "Node: " + str(i)
    print "Pos: " + str(node.getPos())
    print "Adj Nodes: " 
    for adj_node in node.adjacentNodes:
        print "\tNode: " + str(adj_node)
    for adj_dir in node.adjacentNodesDistances:
        print "\tDist: " + str(adj_dir)
    i += 1"""
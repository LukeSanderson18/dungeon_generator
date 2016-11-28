
import re
import math
import random

# if (when) this doesn't work, copy 64 bit Python 3.3 fbx.pyd and fbxsip.pyd from the Autodesk FBX SDK
# into this directory
import fbx

# FbxDouble3 unpacker
def tolist(x):
  return [x[i] for i in range(3)]

# FbxDouble3 packer
def tovec3(x):
  return fbx.FbxDouble3(x[0], x[1], x[2], x[3])

def add3(x, y):
  return [x[i]+y[i] for i in range(3)]

def sub3(x, y):
  return [x[i]+y[i] for i in range(3)]

def neg3(x):
  return [-x[i] for i in range(3)]

def xy_location(x):
  return (int(x[0]+0.5), int(x[1]+0.5))

def rotateZ(v, angle):
  sz = math.sin(angle * (3.14159/180))
  cz = math.cos(angle * (3.14159/180))
  return [
    cz * v[0] - sz * v[1],
    sz * v[0] + cz * v[1],
    0
  ]


class dungeon_generator:
  def __init__(self):  
    self.sdk_manager = fbx.FbxManager.Create()
    if not self.sdk_manager:
      sys.exit(1)
    
    self.io_settings = fbx.FbxIOSettings.Create(self.sdk_manager, fbx.IOSROOT)
    self.sdk_manager.SetIOSettings(self.io_settings)

  def read_components(self):
    importer = fbx.FbxImporter.Create(self.sdk_manager, "")    
    result = importer.Initialize("scenes/components.fbx", -1, self.io_settings)
    if not result:
      raise BaseException("could not find components file")
    self.components = fbx.FbxScene.Create(self.sdk_manager, "")
    result = importer.Import(self.components)
    importer.Destroy()

    root = self.components.GetRootNode()
    top_level = [root.GetChild(i) for i in range(root.GetChildCount())]

    # child nodes matching this pattern are feature markup
    feature_pattern = re.compile('(\<|\>)([^.]+)(\..*)?')

    incoming = self.incoming = {}
    outgoing = self.outgoing = {}
    tiles = self.tiles = {}

    # find the tiles in the file with at least one child (the connectors)
    for node in top_level:
      if node.GetChildCount():
        # for each tile, check the names of the connectors
        tiles[node.GetName()] = node;
        connectors = [node.GetChild(i) for i in range(node.GetChildCount())]
        tile_name = node.GetName()
        print("%s has %d children" % (tile_name, node.GetChildCount()))
        for c in connectors:
          conn_name = c.GetName();
          # use a regular expression to match the connector name
          # and discard any trailing numbers
          match = feature_pattern.match(conn_name)
          if match:
            direction = match.group(1)
            feature_name = match.group(2)
            print("  %s %s %s" % (tile_name, direction, feature_name))
            trans = c.LclTranslation.Get()
            rot = c.LclRotation.Get()
            result = (feature_name, tile_name, trans, rot)

            if direction == '>':
              # outgoing tile indexed by tile_name
              idx = tile_name
              dict = outgoing
            else:
              # incoming tile indexed by feature name
              idx = feature_name
              dict = incoming
            if not idx in dict:
              dict[idx] = []
            dict[idx].append(result)

    # at this point incoming and outgoing index connectors
    # tiles indexes the tiles by name.
    print("self.incoming:", self.incoming)
    print("self.outgoing:", self.outgoing)

  def get_format(self, name):
    reg = self.sdk_manager.GetIOPluginRegistry()
    for idx in range(reg.GetWriterFormatCount()):
      desc = reg.GetWriterFormatDescription(idx)
      print(desc)
      if name in desc:
        return idx
    return -1

  def write_result(self):
    #format = self.get_format("FBX binary")
    format = self.get_format("FBX ascii")

    new_scene = fbx.FbxScene.Create(self.sdk_manager, "result");
    self.create_dungeon(new_scene, "flat")

    exporter = fbx.FbxExporter.Create(self.sdk_manager, "")
    
    if exporter.Initialize("scenes/result.fbx", format, self.io_settings):
      exporter.Export(new_scene)

    exporter.Destroy()

  def make_node(self, new_scene, node_name, pos, angle):
    dest_node = fbx.FbxNode.Create( new_scene, node_name )
    dest_node.SetNodeAttribute(self.tile_meshes[node_name])
    dest_node.LclTranslation.Set(fbx.FbxDouble3(pos[0], pos[1], pos[2]))
    dest_node.LclRotation.Set(fbx.FbxDouble3(0, 0, angle))
    root = new_scene.GetRootNode()
    root.AddChild(dest_node)

  def create_dungeon(self, new_scene, feature_name):
    # clone the tile meshes and name them after their original nodes.
    tile_meshes = self.tile_meshes = {}
    for name in self.tiles:
      tile = self.tiles[name]
      tile_mesh = tile.GetNodeAttribute()
      tile_meshes[name] = tile_mesh.Clone(fbx.FbxObject.eDeepClone, None)
      tile_meshes[name].SetName(name)

    been_here = {}
    pos = (0, 0, 0)
    angle = 0
    out_rot = (0, 0, 0)

    for i in range(40):
      been_here[xy_location(pos)] = 1
      print(been_here, pos)

      # incoming features are indexed on the feature name
      incoming = self.incoming[feature_name]
      in_sel = int(random.randrange(len(incoming)))
      in_feature_name, in_tile_name, in_trans, in_rot = incoming[in_sel]

      # from the feature, set the position and rotation of the new tile
      angle += out_rot[2] - in_rot[2]
      angle = angle + 360 if angle < 0 else angle
      angle = angle - 360 if angle >= 360 else angle
      angle = int(angle + 0.5)
      pos = add3(pos, rotateZ(neg3(in_trans), angle))
      tile_name = in_tile_name
      print(pos, angle, tile_name)

      self.make_node(new_scene, tile_name, pos, angle)

      # outgoing features are indexed on the tile name
      outgoing = self.outgoing[tile_name]
      out_sel = int(random.randrange(len(outgoing)))
      feature_name, out_tile_name, out_trans, out_rot = outgoing[out_sel]

      # find the position of the feature relative to the current object
      pos = add3(pos, rotateZ(out_trans, angle))

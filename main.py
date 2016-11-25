
import FbxCommon
import re
import fbx

if __name__ == '__main__':
  sdk_manager, scene = FbxCommon.InitializeSdkObjects()
  if not FbxCommon.LoadScene(sdk_manager, scene, "scenes/components.fbx"):
    print("error in LoadScene")

  root = scene.GetRootNode()
  top_level = [root.GetChild(i) for i in range(root.GetChildCount())]

  pattern = re.compile('(\<|\>)([^.]+)(\..*)?')

  incoming = {}
  outgoing = {}

  for node in top_level:
    if node.GetChildCount():
      print(node.GetName(), node.GetChildCount())
      connectors = [node.GetChild(i) for i in range(node.GetChildCount())]
      print([c.GetName() for c in connectors])
      for c in connectors:
        name = c.GetName();
        match = pattern.match(name)
        if match:
          direction = match.group(1)
          feature_name = match.group(2)
          print(name, direction, feature_name)
          dict = incoming if direction == '<' else outgoing
          if not feature_name in dict:
            dict[feature_name] = []
          dict[feature_name].append(node)
  print(outgoing)
  print(incoming)            

  write_format = -1
  reg = sdk_manager.GetIOPluginRegistry()
  for idx in range(reg.GetWriterFormatCount()):
    desc = reg.GetWriterFormatDescription(idx)
    if "FBX ascii" in desc:
      write_format = idx

  new_scene = fbx.FbxScene.Create(sdk_manager, "result");
  FbxCommon.SaveScene(sdk_manager, new_scene, "scenes/result.fbx", write_format);

  new_root = new_scene.GetRootNode()
  new_root.AddChild(


XHR = function (action, method, payLoad) {
  var xmlhttp = new XMLHttpRequest()
  xmlhttp.open(method, action, true)
  xmlhttp.setRequestHeader('Content-Type', 'application/json;charset=UTF-8')
  xmlhttp.send(JSON.stringify(payLoad))
  return xmlhttp
}

getCurrentUser = function () {
  var xmlhttp = XHR('/get_current_username', 'GET', null)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      currentUser = (JSON.parse(xmlhttp.responseText))['username']
    }
  }
}

var taskIdChat = 0
var currentUser = getCurrentUser()
var recentMessageId = 0

var addItem = function () {
  var itemToAdd = document.getElementById('newItem').value
  var xmlhttp = XHR('/add', 'POST', [itemToAdd, 0])
  var node = document.createElement('LI')       // adding a copy to the html document
  var textNode = document.createTextNode(itemToAdd)
  node.appendChild(textNode)
  document.getElementById('toDoList').appendChild(node)
  document.getElementById('newItem').value = '' // Clear the text in add text box

  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      buildList(JSON.parse(xmlhttp.responseText))
    }
  }
}

var deleteTask = function (listItem) {
  var payLoad = listItem.id
  var xmlhttp = XHR('/delete', 'POST', payLoad)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      buildList(JSON.parse(xmlhttp.responseText))
    }
  }
}

var assignTask = function (listItem, assignee) {
  var payLoad = [listItem.id, assignee]
  var xmlhttp = XHR('/assign', 'POST', payLoad)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      JSONResponse = JSON.parse(xmlhttp.responseText)
      alert(JSONResponse['alert'])
    }
  }
}

var doUnDo = function (listItem) {
  var taskID = listItem.id
  var taskDone = 0
  if (listItem.style['text-decoration-line'] === 'line-through') { taskDone = 1 }
  var payLoad = [taskID, taskDone]
  var xmlhttp = XHR('/done', 'POST', payLoad)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      parsed_json = JSON.parse(xmlhttp.responseText)

      buildList(parsed_json['created_tasks'])
      buildListAssignedTask(parsed_json['assigned_tasks'])
    }
  }
}

var syncItem = function () {
 syncAssignedTasks()
 syncCreatedTasks()
  
}

var syncAssignedTasks = function(){
  var xmlhttp = XHR('/sync', 'GET', null)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      buildList(JSON.parse(xmlhttp.responseText))
    }
  }
}
var syncCreatedTasks = function(){
  var xmlhttp = XHR('/assigned_to', 'GET', null)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
      buildListAssignedTask(JSON.parse(xmlhttp.responseText))
    }
  }
}

var sendChat = function() {
  var message_input_box = document.getElementById('chat-input')
  var message_text = message_input_box.value
  var payLoad = {'task_id': taskIdChat, 'sender_name': 'current_user', 'message_text': message_text}
  var xmlhttp = XHR('/chat/save_chat', 'POST', payLoad)
  message_input_box.value = ''
}


var discussTask = function (taskId) { // method trigged when discuss method is clicked
  taskIdChat = taskId // updating global taskIdChat based on the click 
  getChat()
}


var getChat = function () {
  payLoad = { 'task_id' : taskIdChat, 'recent_message_id' : recentMessageId } 
  var xmlhttp = XHR('/chat/sync', 'POST', payLoad)
  xmlhttp.onreadystatechange = function () {
    if (xmlhttp.readyState === 4 && xmlhttp.status == 200) {
      buildChat(JSON.parse(xmlhttp.responseText))
      getChat()// polling
    }
  }
}

var buildChat = function (JSONResponse) {
  recentMessageId = JSONResponse[JSONResponse.length - 1]['message_id'] //tacking the recent message ID from recent response
  chatDisplay = document.getElementById('chat-display')
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
  chatDisplay.innerHTML = ''
  for (var x = 0; x < JSONResponse.length; x++) {
    textNode = document.createTextNode(JSONResponse[x]['sender_name'] + ':   ' +  JSONResponse[x]['message_text'] + '\r\n') 
    chatDisplay.appendChild(textNode)
    chatDisplay.appendChild(document.createElement('br'))
  }
}

var createDeleteButton = function(){
    var deleteButton = document.createElement('Button')
    deleteButton.onclick = function () {
      deleteTask(this.parentElement)
    }
    deleteButton.innerHTML = 'Delete'
    return deleteButton
}

var createAssigneeTextBox = function(){
    var assigneeTextBox = document.createElement('input')
    assigneeTextBox.type = 'text'
    return assigneeTextBox
    
}

var createAssigneeButton = function(){
  var assignButton = document.createElement('Button')
  assignButton.onclick = function () {
    assignTask(this.parentElement, this.previousSibling.value)
  }
  assignButton.innerHTML = 'Assign'
  return assignButton
}

var createDiscussButton = function() {
    var discussButton = document.createElement('Button')
    discussButton.onclick = function () {
      discussTask(this.parentElement.id)
    }

    discussButton.innerHTML = 'Discuss'
    return discussButton
}

var buildListAssignedTask = function (JSONResponse) {
  document.getElementById('task-assigned-heading').innerHTML = 'tasks assigned to: ' + currentUser
  var item_list = document.getElementById('task-assigned-list')
  while (item_list.firstChild) {
    item_list.removeChild(item_list.firstChild)
  }

  for (var x = 0; x < JSONResponse.length; x++) {
    var node = document.createElement('LI')
    node.id = (JSONResponse[x][0])

    var doneButton = document.createElement('Button') // done button
    doneButton.onclick = function () {
      doUnDo(this.parentElement)
    }

    if (JSONResponse[x][2] === 1) {
      node.style.textDecoration = 'line-through'
      doneButton.innerHTML = 'un Done'
    } else { doneButton.innerHTML = 'Done' }

    var textNode = document.createTextNode(JSONResponse[x][1])
    node.appendChild(textNode)
    node.appendChild(doneButton)
    document.getElementById('task-assigned-list').appendChild(node)

// delete button
//    node.appendChild(createDeleteButton())
// create assignee textBox and assignee button
//   node.appendChild(createAssigneeTextBox())
//    node.appendChild(createAssigneeButton())
// discuss button
    node.appendChild(createDiscussButton())
  }






























}

var buildList = function (JSONResponse) {
  document.getElementById('main_heading').innerHTML = 'ToDo created by : ' + currentUser
  var item_list = document.getElementById('toDoList')
  while (item_list.firstChild) {
    item_list.removeChild(item_list.firstChild)
  }

  for (var x = 0; x < JSONResponse.length; x++) {
    var node = document.createElement('LI')
    node.id = (JSONResponse[x][0])

    var doneButton = document.createElement('Button') // done button
    doneButton.onclick = function () {
      doUnDo(this.parentElement)
    }

    if (JSONResponse[x][2] === 1) {
      node.style.textDecoration = 'line-through'
      doneButton.innerHTML = 'un Done'
    } else { doneButton.innerHTML = 'Done' }

    var textNode = document.createTextNode(JSONResponse[x][1])
    node.appendChild(textNode)
    node.appendChild(doneButton)
    document.getElementById('toDoList').appendChild(node)

// delete button
    node.appendChild(createDeleteButton())
// create assignee textBox and assignee button
    node.appendChild(createAssigneeTextBox())
    node.appendChild(createAssigneeButton())
// discuss button
    node.appendChild(createDiscussButton())
  }
}

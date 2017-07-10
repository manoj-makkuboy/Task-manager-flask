	var XHR = function(action, method, payLoad){
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.open(method, action);
		xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
		xmlhttp.send(JSON.stringify(payLoad));
		return xmlhttp
	}

	var addItem = function(){	
		var itemToAdd = document.getElementById('newItem').value

		var xmlhttp = XHR("/add", "POST", [itemToAdd, 0]);

		node = document.createElement("LI");       // adding a copy to the html document
		textNode = document.createTextNode(itemToAdd)
		node.appendChild(textNode)
		document.getElementById('toDoList').appendChild(node);	
		document.getElementById('newItem').value = ''		// Clear the text in add text box

		xmlhttp.onreadystatechange = function () {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200){
				buildList(JSON.parse(xmlhttp.responseText));
				}
			}
		}
		
	var deleteTask = function(listItem){
		var payLoad = listItem.id;
		
		var xmlhttp = XHR("/delete", "POST", payLoad);

		xmlhttp.onreadystatechange = function() {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200){
				buildList(JSON.parse(xmlhttp.responseText));
			}
		}
	}


	var assignTask = function(listItem, assignee){
		var payLoad = [listItem.id, assignee];
		
		var xmlhttp = XHR("/assign", "POST", payLoad);

		xmlhttp.onreadystatechange = function() {
			if (xmlhttp.readyState == 4 && xmlhttp.status == 200){
				buildList(JSON.parse(xmlhttp.responseText));
			}
		}
	}


	var doUnDo = function(listItem){
		var taskID = listItem.id
		var taskDone = 0

		if (listItem.style['text-decoration-line'] === 'line-through')
			taskDone = 1	
		
		console.log(taskID,taskDone)
		var payLoad = [taskID, taskDone];	
		var xmlhttp = XHR("/done", "POST", payLoad);

		xmlhttp.onreadystatechange = function () {
			 if (xmlhttp.readyState == 4 && xmlhttp.status == 200){
				 buildList(JSON.parse(xmlhttp.responseText));
			}
	        }
	}

	var syncItem = function(){	
		
		xmlhttp = XHR("/sync", "GET", null);

	        xmlhttp.onreadystatechange = function () {

			 if (xmlhttp.readyState === 4){
				 buildList(JSON.parse(xmlhttp.responseText));
			}
	        }

	
		}
		
	buildList = function(JSONResponse){

		item_list = document.getElementById("toDoList");		
			while(item_list.firstChild){
				item_list.removeChild(item_list.firstChild)	
			}

			for (var x = 0; x < JSONResponse.length; x++){
				var node = document.createElement("LI");
				node.id = ( JSONResponse[x][0] ) 

				var doneButton = document.createElement('Button'); // done button
				doneButton.onclick = function(){
					doUnDo(this.parentElement);};
				
				if(JSONResponse[x][2] == 1){

					node.style.textDecoration = 'line-through';
					doneButton.innerHTML = 'un Done'
				}
				else
					doneButton.innerHTML = 'Done'

					var textNode = document.createTextNode(JSONResponse[x][1]);

					node.appendChild(textNode);
					node.appendChild(doneButton);
					document.getElementById('toDoList').appendChild(node);
									
									// delete button
				var deleteButton = document.createElement('Button'); 
				deleteButton.onclick = function(){
					deleteTask(this.parentElement);};
				
					deleteButton.innerHTML = 'Delete'
					node.appendChild(deleteButton);

						// build textBox
				var assigneeTextBox = document.createElement('input');
				assigneeTextBox.type = "text";
				node.appendChild(assigneeTextBox);

				var assignButton = document.createElement('Button'); 
				assignButton.onclick = function(){
					assignTask(this.parentElement, this.previousSibling.value);};
						
					assignButton.innerHTML = 'Assign'
					node.appendChild(assignButton);

			}
	}



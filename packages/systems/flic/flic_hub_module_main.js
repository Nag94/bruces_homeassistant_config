// main.js
var buttonManager = require("buttons");
var http = require("http");
var url = "http://192.168.xx.xxx:8123/api/events/flic";

buttonManager.on("buttonSingleOrDoubleClickOrHold", function(obj) {
	var button = buttonManager.getButton(obj.bdaddr);
	var clickType = obj.isSingleClick ? "click" : obj.isDoubleClick ? "double_click" : "hold";
	
	http.makeRequest({
		url: url,
		method: "POST",
		headers: {"Content-Type": "application/json", "Authorization": "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
//		content: JSON.stringify({"serial-number": button.serialNumber, "click-type": clickType}),		
		content: JSON.stringify({"button_name": button.name, "click_type": clickType}),				
	}, function(err, res) {
//		console.log("request status: " + res.statusCode);
//		console.log("button_name: " + button.name)
//		console.log("click_type: " + clickType)
	});
});

console.log("Started");

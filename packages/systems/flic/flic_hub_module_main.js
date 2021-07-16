// main.js
var buttonManager = require("buttons");
var http = require("http");
var url = "http://192.168.11.124:8123/api/webhook/flic-abcd1234";

buttonManager.on("buttonSingleOrDoubleClickOrHold", function(obj) {
	var button = buttonManager.getButton(obj.bdaddr);
	var clickType = obj.isSingleClick ? "click" : obj.isDoubleClick ? "double_click" : "hold";
    var buttonId = button.name.replace(" ", "_").toLowerCase();	
	
	http.makeRequest({
		url: url,
		method: "POST",
		headers: {"Content-Type": "application/json"},		
		content: JSON.stringify({"button_name": button.name, "button_id": buttonId, "click_type": clickType, "battery_status": button.batteryStatus }),				
	}, function(err, res) {
//		console.log("request status: " + res.statusCode);
//		console.log("button_name: " + button.name)
//		console.log("click_type: " + clickType)
	});
});

//console.log("Started");
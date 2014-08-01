#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################
# MySensors plugin interface for Indigo 6
#
# Copyright (c)2014-2014 Marcel Trapman.
####################
import httplib, urllib, sys, os, threading, glob, time

kOnlineState = "online"
kOfflineState = "offline"

kBaudrate = 115200

kInterval = 5
kWorkerSleep = 1

kMaxNodeId = 255
kMaxChildId = 255

kNoneNodeId = -1
kNoneChildId = -1
kNoneType = -1

kGatewayNodeId = 0
kGatewayChildId = 0

#MESSAGE message types (M_)
kMessageTypes = {
    "PRESENTATION"          : 0,
    "SET"	                : 1,
    "REQUEST"	            : 2,
    "INTERNAL"	            : 3,
    "STREAM"		        : 4
}

#PRESENTATION sensor types (S_)
kSensorTypes = {
    "DOOR" 			        : [0,  "Door Sensor"],
    "MOTION" 		        : [1,  "Motion Sensor"],
    "SMOKE" 		        : [2,  "Smoke Sensor"],
    "LIGHT" 		        : [3,  "Relay Actuator"],
    "DIMMER" 		        : [4,  "Dimmer Actuator"],
    "COVER" 		        : [5,  "Window Sensor"],
    "TEMP" 			        : [6,  "Temperature Sensor"],
    "HUM" 			        : [7,  "Humidity Sensor"],
    "BARO" 			        : [8,  "Barometer Sensor"],
    "WIND" 			        : [9,  "Wind Sensor"],
    "RAIN" 			        : [10, "Rain Sensor"],
    "UV" 			        : [11, "UV Sensor"],
    "WEIGHT" 		        : [12, "Weight Sensor"],
    "POWER" 		        : [13, "Power Sensor"],
    "HEATER" 		        : [14, "Heater Sensor"],
    "DISTANCE" 		        : [15, "Distance Sensor"],
    "LIGHT_LEVEL"	        : [16, "Luminance Sensor"],
    "ARDUINO_NODE"	        : [17, "Arduino Node"],
    "ARDUINO_RELAY"	        : [18, "Arduino Repeater"],
    "LOCK" 			        : [19, "Lock Sensor"],
    "IR" 			        : [20, "IR Sensor"],
    "WATER" 		        : [21, "Water Sensor"],
	"AIR_QUALITY"           : [22, "AirQuality Sensor"]
}

#SET_VARIABLE, REQ_VARIABLE, ACK_VARIABLE sensor variables (V_)
kVariableTypes = {
    "TEMP"			        : [0,  "temperature",               "temperture update to"],
    "HUM"			        : [1,  "humidity",                  "humidity update to"],
    "LIGHT"			        : [2,  "onOffState",                "state update to"],
    "DIMMER"		        : [3,  "dimmer",                    "dimmer update to"],
    "PRESSURE"		        : [4,  "barometer",                 "pressure update to"],
    "FORECAST"		        : [5,  "barometer",                 "forecast update to"],
    "RAIN"			        : [6,  "rain",                      "rain update to"],
    "RAINRATE"		        : [7,  "rain",                      "rainrate update to"],
    "WIND"			        : [8,  "wind",                      "wind update to"],
    "GUST"			        : [9,  "wind",                      "gust update to"],
    "DIRECTION"		        : [10, "direction",                 "direction update to"],
    "UV"			        : [11, "uv",                        "uv update to"],
    "WEIGHT"		        : [12, "scale",                     "scale update to"],
    "DISTANCE"		        : [13, "distance",                  "distance update to"],
    "IMPEDANCE"		        : [14, "scale",                     "scale update to"],
    "ARMED"			        : [15, "security",                  "security update to"],
    "TRIPPED"		        : [16, "onoroff",                   "state update to"],
    "WATT"			        : [17, "energy",                    "watt update to"],
    "KWH"			        : [18, "energy",                    "kwh update to"],
    "SCENE_ON"		        : [19, "scene",                     "scene on state update to"],
    "SCENE_OFF"		        : [20, "scene",                     "scene off state update to"],
    "HEATER"		        : [21, "user",                      "heater user update to"],
    "HEATER_SW"		        : [22, "onoroff",                   "heater state update to"],
    "LIGHT_LEVEL"	        : [23, "light",                     "luminance update to"],
    "VAR_1"			        : [24, "var",                       "var 1 update to"],
    "VAR_2"			        : [25, "var",                       "var 2 update to"],
    "VAR_3"			        : [26, "var",                       "var 3 update to"],
    "VAR_4"			        : [27, "var",                       "var 4 update to"],
    "VAR_5"			        : [28, "var",                       "var 5 update to"],
    "UP"			        : [29, "door",                      "up update to"],
    "DOWN"			        : [30, "door",                      "down update to"],
    "STOP"			        : [31, "door",                      "stop update to"],
    "IR_SEND"		        : [32, "ir",                        "ir send update to"],
    "IR_RECEIVE"	        : [33, "ir",                        "ir receive update to"],
    "FLOW"			        : [34, "water",                     "water flow update to"],
    "VOLUME"		        : [35, "water",                     "water volume update to"],
    "LOCK_STATUS"	        : [36, "lock",                      "lock status update to"]
}

#INTERNAL internal messages (I_)
kInternalTypes = {
    "BATTERY_LEVEL"	        : [0,  "battery level ",            "update to "],
    "TIME"			        : [1,  "time ",                     "update to "],
    "VERSION"		        : [2,  "Arduino library version ",  "update to "],
    "ID_REQUEST"            : [3,  "ID request ",               ""],
 	"ID_RESPONSE"           : [4,  "ID response ",              ""],
 	"INCLUSION_MODE"        : [5,  "inclusion mode ",           "update to "],
  	"CONFIG"                : [6,  "config ",                   "update to "],
    "PING"			        : [7,  "ping ",                     ""],
    "PING_ACK"		        : [8,  "Ping ACK ",                 ""],
    "LOG_MESSAGE"	        : [9,  "Log message ",              ""],
    "CHILDREN"		        : [10, "Children ",                 "update to "],
    "SKETCH_NAME"	        : [11, "Sketch name ",              "udate to "],
    "SKETCH_VERSION"        : [12, "Sketch version ",           "update to "]
}

class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.debug                  = False
        self.inclusionMode          = False

        self.connection             = None
        self.connectionAttempts     = 0

        self.interval               = kInterval

        self.devices                = indigo.Dict()
        self.nodeIds                = indigo.Dict()

        self.gatewayAvailable       = False
        self.gatewayVersion         = None

    def __del__(self):
        indigo.PluginBase.__del__(self)

    def startup(self):
        self.debug = self.pluginPrefs.get("showDebugInfo", False)

        self.debugLog(u"Connecting...")

        self.address = self.pluginPrefs["address"]
        self.unit = self.pluginPrefs.get("unit", "M")

        result = False

        while not result and self.connectionAttempts < 6:
            result = self.openConnection()

            self.sleep(kWorkerSleep)

        if not result:
            self.errorLog(u"permanently failed connecting Gateway at address: %s" % self.address)

        self.loadDevices()

    def shutdown(self):
        self.debugLog(u"Disconnecting...")

        if self.connection:
            self.connection.close()

    def deviceStartComm(self, indigoDevice):
        self.debugLog(u"Device started: \"%s\" %s" % (indigoDevice.name, indigoDevice.id))
        pass

    def deviceStopComm(self, indigoDevice):
        self.debugLog(u"Device stopped: \"%s\" %s" % (indigoDevice.name, indigoDevice.id))

        try:
            deviceId = indigoDevice.id

            if not deviceId in indigo.devices:
                properties = indigoDevice.pluginProps

                address = self.getAddress(address = properties["address"])

                device = self.devices[address]

                device["id"] = ""

                self.devices[address] = device
        except Exception, (ErrorMessage):
            pass

    def didDeviceCommPropertyChange(self, oldIndigoDevice, indigoDevice):
        return True

    def update(self):
        self.debugLog(u"Update method called")

        try:
            self.readMessage()
        except reference.CommandError:
            pass

    def runConcurrentThread(self):
        self.debugLog(u"Running thread")

        try:
            while True:
                if self.connection and self.connection.isOpen():
                    self.processIncoming()

                self.sleep(self.interval)
        except self.StopThread:
            pass

    ########################################
    # DeviceFactory methods (specified in Devices.xml)
    ########################################
    def getDeviceGroupList(self, filter, valuesDict, deviceIdList):
        menuItems = []

        for deviceId in deviceIdList:
            if deviceId in indigo.devices:
                indigoDevice = indigo.devices[deviceId]

                deviceName = indigoDevice.name
            else:
                deviceName = u"- device not found -"

            menuItems.append((deviceId, deviceName))

        return menuItems

    def getVariableValue(self, field, value):
        if not field:
            return None

        if field == "onOffState":
            if value == None:
                return 0
            else:
                return int(value)

        return None

    def getAvailableDevices(self, filter, valuesDict, deviceIdList):
        menuItems = []

        for address in self.devices:
            device = self.devices[address]

            identifiers = self.getIdentifiers(address)

            nodeId = identifiers[0]
            childId = identifiers[1]

            type = device["type"]

            try:
                if nodeId != kGatewayNodeId and nodeId != kMaxNodeId:
                    if (type == self.getSensorNumber("ARDUINO_RELAY") and not device["id"]) or (type == self.getSensorNumber("ARDUINO_NODE") and self.hasChildren(nodeId)):
                        deviceName = "%s" % nodeId

                        if device["model"]:
                            deviceName = "%s - %s" % (deviceName, device["model"])
                        elif self.getSensorName(device["type"]):
                            deviceName = "%s - %s" % (deviceName, self.getSensorName(device["type"]))
                        else:
                            deviceName = "%s - %s" % (deviceName, "unknown")

                        if device["modelVersion"]:
                            deviceName = "%s (SK%s)" % (deviceName, device["modelVersion"])

                        menuItems.append((nodeId, deviceName))
                    elif type == kNoneType:
                        self.debugLog(u"device %s:%s not available: no type set" % (nodeId, childId))
            except Exception, (ErrorMessage):
                pass

        return menuItems

    def addIndigoDevice(self, valuesDict, deviceIdList):
        try:
            nodeId = kNoneNodeId

            try:
                nodeId = int(valuesDict["selecteddevice"])

                self.debugLog(u"add device %s" % nodeId)
            except Exception, (ErrorMessage):
                pass

            if nodeId > kNoneNodeId:
                self.addIndigoChildren(nodeId)
        except Exception, (ErrorMessage):
            pass

        return valuesDict

    def getDeviceFactoryUiValues(self, devIdList):
        valuesDict = indigo.Dict()
        errorMsgDict = indigo.Dict()

        return (valuesDict, errorMsgDict)

    def validateDeviceFactoryUi(self, valuesDict, devIdList):
        errorsDict = indigo.Dict()

        return (True, valuesDict, errorsDict)

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        return (True, valuesDict)

    def closedDeviceFactoryUi(self, valuesDict, userCancelled, devIdList):
        return

    def validatePrefsConfigUi(self, valuesDict):
        return True

    def actionControlDimmerRelay(self, pluginAction, indigoDevice):
        try:
            properties = indigoDevice.pluginProps

            address = properties["address"]

            identifiers = self.getIdentifiers(address)

            nodeId = identifiers[0]
            childId = identifiers[1]

            if pluginAction.deviceAction == indigo.kDimmerRelayAction.TurnOn:
                onOffState = True
            elif pluginAction.deviceAction == indigo.kDimmerRelayAction.TurnOff:
                onOffState = False
            elif pluginAction.deviceAction == indigo.kDimmerRelayAction.Toggle:
                onOffState = not indigoDevice.onState

            self.updateState(indigoDevice, "LIGHT", onOffState)

            if onOffState:
                value = 1
            else:
                value = 0

            self.sendSetCommand(nodeId, childId, "LIGHT", value)
        except Exception, (ErrorMessage):
			self.errorLog(u"dimmer action failed: %s" % ErrorMessage)

    ########################################
    # actions
    ########################################
    def send(self, pluginAction):
        self.debugLog(u"Send method called")

    ########################################
    # events
    ########################################
    def triggerStartProcessing(self, trigger):
        status = trigger.pluginProps["status"]

        self.debugLog(u"Start processing trigger: %s for: %s status: %s" % (unicode(trigger.id), "sensor", status))

        triggerType = trigger.pluginTypeId

    def triggerStopProcessing(self, trigger):
        status = trigger.pluginProps["status"]

        self.debugLog(u"Stop processing trigger: %s for: %s status: %s" % (unicode(trigger.id), "sensor", status))

        triggerType = trigger.pluginTypeId

    ########################################
    # Incoming messages
    ########################################
    def processIncoming(self):
        arguments = None

        request = None
        nodeId = kMaxNodeId
        childId = kNoneChildId
        messageType = kNoneType
        itemType = kNoneType
        payload = ""

        try:
            request = self.connection.readline()

            if request:
                request = request.strip("\n\r")

            if len(request) == 0:
                return

            self.debugLog(u"receive raw %s" % request)

            if request[0].isalpha() or request.find(";") == kNoneType or request.count(";") < 4:
                raise Exception("wrong request formatting: %s" % request)

            arguments = request.split(";")

            nodeId = int(arguments[0])
            childId = int(arguments[1])
            messageType = int(arguments[2])
            itemType = int(arguments[3])
            payload = ";".join(arguments[4:])

            if payload.startswith("read:") or payload.startswith("send:"):
                pass
            elif messageType == self.getMessageNumber("PRESENTATION"):
                self.processPresentationCommand(nodeId, childId, itemType, payload)
            elif messageType == self.getMessageNumber("SET"):
                self.processSetCommand(nodeId, childId, itemType, payload)
            elif messageType == self.getMessageNumber("REQUEST"):
                self.processRequestCommand(nodeId, childId, itemType, payload)
            elif messageType == self.getMessageNumber("INTERNAL"):
                self.processInternalCommand(nodeId, childId, itemType, payload)
            elif messageType == self.getMessageNumber("STREAM"):
                self.processStreamCommand(nodeId, childId, itemType, payload)
            else:
                raise Exception("Unrecognized messageType %s" % messageType)
        except Exception, (ErrorMessage):
            self.errorLog(u"process incoming failed: %s" % ErrorMessage)

            if "serial" in ErrorMessage:
                self.connection = None

    def processPresentationCommand(self, nodeId, childId, itemType, payload):
        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        name = self.getSensorName(itemType)

        try:
            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if device:
                device = self.updateDevice(device, address, { "type" : itemType, "model" : name, "version" : payload })

            if indigoDevice:
                self.updateProperties(indigoDevice, { "type" : itemType, "model" : name, "version" : payload })

                indigo.server.log(u"received '%s' %s version update to %s" % (indigoDevice.name, name, payload))
            else:
                indigo.server.log(u"received '%s:%s' %s version update to %s" % (nodeId, childId, name, payload))
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"received '%s' %s version update to %s failed: %s" % (indigoDevice.name, name, payload, ErrorMessage))
            else:
                self.errorLog(u"received '%s:%s' %s version update to %s failed: %s" % (nodeId, childId, name, payload, ErrorMessage))

    def processSetCommand(self, nodeId, childId, itemType, payload):
        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        text = self.getVariableText(itemType)

        try:
            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if indigoDevice:
                self.updateState(indigoDevice, itemType, payload)

                indigo.server.log(u"received '%s' %s %s" % (indigoDevice.name, text, payload))
            else:
                indigo.server.log(u"received '%s:%s' %s %s" % (nodeId, childId, text, payload))
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"received '%s' %s %s failed: %s" % (indigoDevice.name, text, payload, ErrorMessage))
            else:
                self.errorLog(u"received '%s:%s' %s %s failed: %s" % (nodeId, childId, text, payload, ErrorMessage))

    def processRequestCommand(self, nodeId, childId, itemType, payload):
        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        field = self.getVariableField(itemType)
        text = self.getVariableText(itemType)

        try:
            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if indigoDevice:
                value = indigoDevice.states[field]

                value = self.getVariableValue(field, value)

                if value is not None:
                    self.sendStreamCommand(nodeId, childId, itemType, value)

                indigo.server.log(u"received status request for '%s:%s' %s %s" % (nodeId, childId, text, payload))
            else:
                indigo.server.log(u"received status request for '%s' %s %s" % (indigoDevice.name, text, payload))
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"received status request for '%s' %s %s failed: %s" % (indigoDevice.name, text, payload, ErrorMessage))
            else:
                self.errorLog(u"received status request for '%s:%s' %s %s failed: %s" % (nodeId, childId, text, payload, ErrorMessage))

    def processStreamCommand(self, nodeId, childId, itemType, payload):
        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        try:
            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if indigoDevice:
                indigo.server.log(u"received stream request for '%s:%s' %s" % (nodeId, childId, payload))
            else:
                indigo.server.log(u"received stream request for '%s' %s" % (indigoDevice.name, payload))
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"received stream request for '%s' %s failed: %s" % (indigoDevice.name, payload, ErrorMessage))
            else:
                self.errorLog(u"received stream request for '%s:%s' %s failed: %s" % (nodeId, childId, payload, ErrorMessage))

    def processInternalCommand(self, nodeId, childId, itemType, payload):
        if itemType == self.getInternalNumber("BATTERY_LEVEL"):
            childId = 0

        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        name = self.getInternalName(itemType)
        text = self.getInternalText(itemType)

        try:
            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if itemType == self.getInternalNumber("BATTERY_LEVEL"):
                # 0
                self.updateProperties(indigoDevice, { "SupportsBatteryLevel" : True })

                self.updateState(indigoDevice, "batteryLevel", payload)
            elif itemType == self.getInternalNumber("TIME"):
                # 1
                self.sendInternalCommand(nodeId, childId, itemType, time.time())
            elif itemType == self.getInternalNumber("VERSION"):
                # 2
                self.updateDevice(device, address, { "version" : payload })

                if nodeId == kGatewayNodeId and childId == kGatewayChildId:
                    self.gatewayVersion = device["version"]

                self.updateProperties(indigoDevice, { "version" : payload})

                self.updateState(indigoDevice, "state", kOnlineState)
            elif itemType == self.getInternalNumber("ID_REQUEST"):
                # 3
                self.sendInternalCommand(nodeId, childId, "ID_RESPONSE", self.nextAvailableNodeId())
                pass
            elif itemType == self.getInternalNumber("ID_RESPONSE"):
                # 4 Ignore
                pass
            elif itemType == self.getInternalNumber("INCLUSION_MODE"):
                # 5
                if nodeId == kGatewayNodeId and childId == kGatewayChildId:
                    if payload == "1":
                        self.inclusionMode = True
                    else:
                        self.inclusionMode = False
            elif itemType == self.getInternalNumber("CONFIG"):
                # 6
                self.sendInternalCommand(nodeId, childId, itemType, self.unit)
                pass
            elif itemType == self.getInternalNumber("PING"):
                # 7 Ignore
                pass
            elif itemType == self.getInternalNumber("PING_ACK"):
                # 8 Ignore
                pass
            elif itemType == self.getInternalNumber("LOG_MESSAGE"):
                # 9
                if "Arduino startup complete" in payload:
                    self.updateState(indigoDevice, "state", kOnlineState)

                    self.gatewayAvailable = True

                name = ""
            elif itemType == self.getInternalNumber("CHILDREN"):
                # 10
                self.updateProperties(indigoDevice, { "children" : payload })
            elif itemType == self.getInternalNumber("SKETCH_NAME"):
                # 11
                self.updateDevice(device, address, { "model" : payload })

                self.updateProperties(indigoDevice, { "model" : payload })
            elif itemType == self.getInternalNumber("SKETCH_VERSION"):
                # 12
                self.updateDevice(device, address, { "modelVersion" : payload })

                self.updateProperties(indigoDevice, { "modelVersion" : payload })
            else:
                raise Exception("item type not found")

            if indigoDevice:
                indigo.server.log(u"received '%s' %s%s%s" % (indigoDevice.name, name, text, payload))
            else:
                indigo.server.log(u"received '%s:%s' %s%s%s" % (nodeId, childId, name, text, payload))
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"received '%s' %s%s%s failed: %s" % (indigoDevice.name, name, text, payload, ErrorMessage))
            else:
                self.errorLog(u"received '%s:%s' %s%s%s failed: %s" % (nodeId, childId, name, text, payload, ErrorMessage))

    ########################################
    # Outgoing messages
    ########################################
    def sendStreamCommand(self, nodeId, childId, itemType, value):
        field = self.getVariableField(itemType)
        type = self.getVariableNumber(itemType)

        uiValue = self.uiValue(field, type, value)

        self.sendCommand(nodeId, childId, "STREAM", type, value, uiValue)

    def sendSetCommand(self, nodeId, childId, itemType, value):
        field = self.getVariableField(itemType)
        type = self.getVariableNumber(itemType)

        uiValue = self.uiValue(field, type, value)

        self.sendCommand(nodeId, childId, "SET", 1, type, value, uiValue)

    def sendRequestResponse(self, nodeId, childId, itemType, value):
        field = self.getVariableField(itemType)
        type = self.getVariableNumber(itemType)

        uiValue = self.uiValue(field, type, value)

        self.sendCommand(nodeId, childId, "SET", 1, type, value, uiValue)

    def sendInternalCommand(self, nodeId, childId, itemType, value):
        name = self.getInternalName(itemType)
        type = self.getInternalNumber(itemType)

        uiValue = self.uiValue(name, type, value)

        self.sendCommand(nodeId, childId, "INTERNAL", 0, type, value, uiValue)

    def sendCommand(self, nodeId, childId, messageType, ack, itemType, value, uiValue):
        address = self.getAddress(nodeId = nodeId, childId = childId)

        device = self.getDevice(address = address)

        indigoDevice = None

        messageType = self.getMessageNumber(messageType)

        try:
            command = "%s;%s;%s;%s;%s;%s" % (nodeId, childId, messageType, ack, itemType, value)

            self.debugLog(u"command %s" % command)

            if device and device["id"]:
                indigoDevice = indigo.devices[device["id"]]

            if self.connection and self.connection.writable:
                self.connection.write(command + "\n")

                if indigoDevice:
                    indigo.server.log(u"sent '%s' %s " % (indigoDevice.name, uiValue))
                else:
                    indigo.server.log(u"sent '%s:%s' %s " % (nodeId, childId, uiValue))

                    return True
            else:
               raise Exception("Can't write to serial port")
        except Exception, (ErrorMessage):
            if indigoDevice:
                self.errorLog(u"send '%s' %s failed: %s" % (indigoDevice.name, uiValue, ErrorMessage))
            else:
                self.errorLog(u"send '%s:%s' %s failed: %s" % (nodeId, childId, uiValue, ErrorMessage))

        return False

    ########################################
    # Action methods
    ########################################



    ########################################
    # Device methods
    ########################################
    def getDevice(self, indigoDevice = None, nodeId = None, childId = None, address = None):
        if not address:
            address = self.getAddress(nodeId = nodeId, childId = childId)
        else:
            address = self.getAddress(address = address)

        if nodeId == kNoneNodeId or childId == kNoneChildId or nodeId == kMaxNodeId or childId == kMaxChildId:
            self.debugLog(u"get device %s:%s skipped" % nodeId, childId)

            return None

        self.debugLog(u"get device %s" % address)

        if not address in self.devices:
            if not nodeId:
                identifiers = self.getIdentifiers(address)

                nodeId = identifiers[0]
                childId = identifiers[1]

            device = self.createDevice(nodeId, childId, address)

            self.sendInternalCommand(nodeId, childId, "VERSION", "Get Version")

            if nodeId != kGatewayNodeId:
                self.sendInternalCommand(nodeId, childId, "SKETCH_NAME", "Get Sketch Name")
        else:
            device = self.devices[address]

            if indigoDevice:
                properties = { "id" : indigoDevice.id }

                self.updateDevice(device, address, properties)

        if address in self.devices:
            return self.devices[address]
        else:
            return None

    def createDevice(self, nodeId, childId, address):
        device = indigo.Dict()

        self.debugLog(u"create device %s" % address)

        if nodeId == 0:
            device["type"] = self.getSensorNumber("ARDUINO_NODE")
        else:
            device["type"] = kNoneType

        device["version"] = ""
        device["id"] = ""
        device["model"] = self.getSensorName(device["type"])
        device["modelVersion"] = ""

        self.devices[address] = device

        self.pluginPrefs["devices"] = self.devices

        self.updateNodeIds(nodeId, False)

    def updateDevice(self, device, address, properties):
        if not device:
            return

        updated = False

        for property in properties:
            if not property in device:
                self.debugLog(u"update device %s created %s = '%s'" % (address, property, properties[property]))

                device[property] = properties[property]

                updated = True
            elif device[property] != properties[property]:
                self.debugLog(u"update device %s updated %s = '%s'" % (address, property, properties[property]))

                device[property] = properties[property]

                updated = True

        if updated:
            self.devices[address] = device

            self.pluginPrefs["devices"] = self.devices

        return device

    def updateNodeIds(self, nodeId, value):
        if nodeId == kMaxNodeId:
            return

        id = "N%s" % nodeId

        if self.nodeIds[id] != value:
            self.nodeIds[id] = value

            self.pluginPrefs["nodeIds"] = self.nodeIds

    def updateState(self, indigoDevice, itemType, payload):
        if not indigoDevice:
            return

        text = self.getVariableText(itemType)
        field = self.getVariableField(itemType)

        uiValue = None

        if itemType == "batteryLevel":
            field = itemType
            value = int(payload)
            uiValue = u"%s%%" % payload
        elif field == "temperature":
            value = float(payload)

            if self.unit == "M":
                uiValue = u"%.1f °C" % value
            else:
                uiValue = u"%.1f °F" % value
        elif field == "onOffState":
            value = self.booleanValue(payload)
        elif field == "onoroff":
            value = self.booleanValue(payload)

            if value:
                uiValue = u"on"
            else:
                uiValue = u"off"
        else:
            value = str(payload)

        if indigoDevice:
            if itemType == "batteryLevel" or value != indigoDevice.states[field]:
                if uiValue:
                    indigoDevice.updateStateOnServer(field, value = value, uiValue = uiValue)

                    return u"%s %s" % (text, uiValue)
                else:
                    indigoDevice.updateStateOnServer(field, value = value)

                    return u"%s %s" % (text, value)

        return None

    def updateProperties(self, indigoDevice, properties):
        if not indigoDevice:
            return

        indigoProperties = indigoDevice.pluginProps

        for property in properties:
            if hasattr(indigoProperties, property) and indigoProperties[property] == properties[property]:
                del properties[property]

        if len(properties) > 0:
            indigoProperties.update(properties)
            indigoDevice.replacePluginPropsOnServer(indigoProperties)

    def hasDeviceId(self, selectedNodeId):
        for address in self.devices:
            device = self.devices[address]

            identifiers = self.getIdentifiers(address)

            nodeId = identifiers[0]
            childId = identifiers[1]

            if nodeId == selectedNodeId and device["id"]:
                return True

        return False

    def hasChildren(self, selectedNodeId):
        count = 0

        for address in self.devices:
            try:
                device = self.devices[address]

                identifiers = self.getIdentifiers(address)

                nodeId = identifiers[0]

                if nodeId == selectedNodeId and not device["id"]:
                    count = count + 1
            except Exception:
                pass

        return False if count < 2 else True

    def addIndigoChildren(self, selectedNodeId):
        if selectedNodeId == 0:
            boardAddress = self.getAddress(nodeId = selectedNodeId, childId = 0)
        else:
            boardAddress = self.getAddress(nodeId = selectedNodeId, childId = kMaxChildId)

        board = self.getDevice(address = boardAddress)

        for address in self.devices:
            try:
                identifiers = self.getIdentifiers(address)

                nodeId = identifiers[0]
                childId = identifiers[1]

                device = self.getDevice(address = address)

                if selectedNodeId == nodeId and (address != boardAddress or device["type"] == self.getSensorNumber("ARDUINO_RELAY")):
                    deviceName = self.getSensorName(device["type"])
                    deviceType = self.getSensorKey(device["type"])

                    indigoDevice = indigo.device.create(indigo.kProtocol.Plugin, deviceTypeId = deviceType)

                    if board["model"]:
                        boardModel = board["model"]
                    else:
                        boardModel = self.getSensorName(board["type"])

                    if board["modelVersion"]:
                        indigoDevice.model = ("%s (SK%s)" % (boardModel, board["modelVersion"]))
                    else:
                        indigoDevice.model = ("%s" % boardModel)

                    indigoDevice.subModel = deviceName

                    indigoDevice.replaceOnServer()

                    self.updateDevice(device, address, { "id" : indigoDevice.id })

                    properties = dict()

                    if address:
                        properties["address"] = self.formatAddress(address)
                    else:
                        properties["address"] = ""

                    if deviceType:
                        properties["deviceType"] = self.getSensorNumber(device["type"])
                    else:
                        properties["deviceType"] = kNoneType

                    if device["version"]:
                        properties["version"] = device["version"]
                    else:
                        properties["version"] = ""

                    if indigoDevice.model:
                        properties["model"] = indigoDevice.model
                    else:
                        properties["model"] = ""

                    self.updateProperties(indigoDevice, properties)
            except Exception, (ErrorMessage):
                self.errorLog(u"add children failed: %s" % ErrorMessage)

    def loadDevices(self):
        if "devices" in self.pluginPrefs:
            self.devices = self.pluginPrefs["devices"]

        if "nodeIds" in self.pluginPrefs:
            self.nodeIds = self.pluginPrefs["nodeIds"]
        else:
            self.setupNodeIds()

        try:
            for address in self.devices:
                 try:
                    device = self.devices[address]

                    self.debugLog(u"available device\n%s" % device)

                    identifiers = self.getIdentifiers(address)

                    nodeId = identifiers[0]
                    childId = identifiers[1]

                    deviceId = device["id"]

                    if not deviceId in indigo.devices:
                        self.updateDevice(device, address, { "id" : "" })

                    if self.connection and self.connection.isOpen():
                        if nodeId == kGatewayNodeId and childId == kGatewayChildId:
                            self.gatewayVersion = device["version"]

                            self.sendInternalCommand(nodeId, childId, "VERSION", "Get Version")
                        elif device["type"] == kNoneType:
                            self.sendInternalCommand(nodeId, childId, "VERSION", "Get Version")
                            self.sendInternalCommand(nodeId, childId, "SKETCH_NAME", "Get Sketch Name")
                 except Exception, (ErrorMessage):
                    pass

            for deviceId in indigo.devices.iter("self"):
                try:
                    indigoDevice = indigo.devices[deviceId]

                    self.debugLog(u"used device\n%s" % indigoDevice)

                    if indigoDevice.address:
                        address = self.getAddress(address = indigoDevice.address)

                        device = self.getDevice(indigoDevice, address = address)

                    if not (self.connection and self.connection.isOpen()):
                        indigoDevice.setErrorStateOnServer(kOfflineState)
                except Exception, (ErrorMessage):
                    pass
        except Exception, (ErrorMessage):
            self.errorLog(u"load devices failed %s" % ErrorMessage)

        self.debugLog(u"found %s available devices" % len(self.devices))

    ########################################
    # Lookup methods
    ########################################
    def getMessageNumber(self, itemType):
        if isinstance(itemType, int):
            return itemType
        elif itemType in kMessageTypes:
            return kMessageTypes[itemType]

        return kNoneType

    def getMessageKey(self, itemType):
        if isinstance(itemType, int):
            for key in kMessageTypes:
                if kMessageTypes[key][0] == itemType:
                    return key
        elif itemType in kMessageTypes:
            return itemType

        return None

    def getSensorNumber(self, itemType):
        if isinstance(itemType, int):
            return itemType
        elif itemType in kSensorTypes:
            return kSensorTypes[itemType][0]

        return kNoneType

    def getSensorName(self, itemType):
        if isinstance(itemType, int):
            for key in kSensorTypes:
                if kSensorTypes[key][0] == itemType:
                    return kSensorTypes[key][1]
        elif itemType in kSensorTypes:
            return kSensorTypes[itemType][1]

        return ""

    def getSensorKey(self, itemType):
        if isinstance(itemType, int):
            for key in kSensorTypes:
                if kSensorTypes[key][0] == itemType:
                    return key
        elif itemType in kSensorTypes:
            return itemType

        return None

    def getVariableNumber(self, itemType):
        if isinstance(itemType, int):
            return itemType
        elif itemType in kVariableTypes:
            return kVariableTypes[itemType][0]

        return kNoneType

    def getVariableField(self, itemType):
        if isinstance(itemType, int):
            for key in kVariableTypes:
                if kVariableTypes[key][0] == itemType:
                    return kVariableTypes[key][1]
        elif itemType in kVariableTypes:
            return kVariableTypes[itemType][1]

        return None

    def getVariableText(self, itemType):
        if isinstance(itemType, int):
            for key in kVariableTypes:
                if kVariableTypes[key][0] == itemType:
                    return kVariableTypes[key][2]
        elif itemType in kVariableTypes:
            return kVariableTypes[itemType][2]

        return None

    def getVariableKey(self, itemType):
        if isinstance(itemType, int):
            for key in kVariableTypes:
                if kVariableTypes[key][0] == itemType:
                    return key
        elif itemType in kVariableTypes:
            return itemType

        return None

    def getInternalNumber(self, itemType):
        if isinstance(itemType, int):
            return itemType
        elif itemType in kInternalTypes:
            return kInternalTypes[itemType][0]

        return kNoneType

    def getInternalText(self, itemType):
        if isinstance(itemType, int):
            for key in kInternalTypes:
                if kInternalTypes[key][0] == itemType:
                    return kInternalTypes[key][2]
        elif itemType in kInternalTypes:
            return kInternalTypes[itemType][2]

        return None

    def getInternalName(self, itemType):
        if isinstance(itemType, int):
            for key in kInternalTypes:
                if kInternalTypes[key][0] == itemType:
                    return kInternalTypes[key][1]
        elif itemType in kInternalTypes:
            return kInternalTypes[itemType][1]

        return None

    def getInternalKey(self, itemType):
        if isinstance(itemType, int):
            for key in kInternalTypes:
                if kInternalTypes[key][0] == itemType:
                    return key
        elif itemType in kInternalTypes:
            return itemType

        return None

    def nextAvailableNodeId(self):
        for nodeId in range(1, kMaxNodeId):
            id = "N%s" % nodeId

            if self.nodeIds[id] and self.nodeIds[id] < kMaxNodeId:
                return nodeId

        return kMaxNodeId

    ########################################
    # Helper methods
    ########################################
    def getAddress(self, nodeId = None, childId = None, address = None):
        if address:
            try:
                identifiers = self.getIdentifiers(address)

                nodeId = identifiers[0]
                childId = identifiers[1]
            except Exception, (ErrorMessage):
                pass

        return "N%sC%s" % (nodeId, childId)

    def getIdentifiers(self, address):
        if address:
            if address[0].isalpha():
                try:
                    identifiers = address[1:].split("C")

                    return [ int(identifiers[0]), int(identifiers[1]) ]
                except Exception, (ErrorMessage):
                    pass
            elif ":" in address:
                try:
                    identifiers = address.split(":")

                    return [ int(identifiers[0]), int(identifiers[1]) ]
                except Exception, (ErrorMessage):
                    pass

        return None

    def formatAddress(self, address):
        try:
            identifiers = self.getIdentifiers(address)

            return "%s:%s" % (identifiers[0], identifiers[1])
        except Exception, (ErrorMessage):
            pass

        return ""

    def setupNodeIds(self):
        for index in range(0, kMaxNodeId):
            id = "N%s" % index

            self.nodeIds[id] = True

        self.updateNodeIds(0, False)

    def booleanValue(self, value):
        try:
            if isinstance(value, int) or isinstance(value, float):
                return value > 0
            elif isinstance(value, str):
                return value.lower() in [ "yes", "true", "t", "1" ]
            elif type(value) is bool:
                return value
        except Exception, (ErrorMessage):
            pass

        return None

    def numberValue(self, value):
        try:
            if isinstance(value, int):
                return int(value)
            elif isinstance(value, float):
                return float(value)
            elif type(value) is bool:
                if value:
                    return 1
                else:
                    return 0
        except Exception, (ErrorMessage):
            pass

        return None

    def integerValue(self, value):
        try:
            if isinstance(value, int):
                return int(value)
            elif isinstance(value, float):
                return int(float(value + 0.5))
            elif type(value) is bool:
                if value:
                    return 1
                else:
                    return 0
            elif type(value) is str:
                try:
                    return int(value)
                except ValueError:
                    return int(float(value + 0.5))
        except Exception, (ErrorMessage):
            pass

        return None

    def uiValue(self, field, type, value):
        if not field or not type or not value:
            uiValue = ""
        if type == "batteryLevel":
            uiValue = u"%s%%" % value
        elif field == "temperature":
            value = float(value)

            if self.unit == "M":
                uiValue = u"%.1f °C" % value
            else:
                uiValue = u"%.1f °F" % value
        elif field == "onOffState" or field == "onoroff":
            value = self.booleanValue(value)

            if value:
                uiValue = u"on"
            else:
                uiValue = u"off"
        elif value:
            uiValue = str(value)
        else:
            uiValue = ""

        return uiValue

    ########################################
    # Start connecting
    ########################################
    def openConnection(self):
        if self.address:
            self.connection = self.openSerial("com.it2be.indigo.mysensors", portUrl = self.address, baudrate = kBaudrate, timeout = 0)
        else:
            self.address = "undefined"

        if self.connection:
            self.connectionAttempts = 0

            indigo.server.log(u"connected to Gateway on %s" % self.address)

            return True
        else:
            self.connectionAttempts = self.connectionAttempts + 1

            return False

    ########################################
    # Config Methods
    ########################################
    def loadSerialPorts(self, filter = "", valuesDict = None, typeId = "", targetId = 0):
        self.debugLog(u"Ports loading")

        returnList = list()

        if not valuesDict:
            valuesDict = {}

        portList = glob.glob("/dev/tty.*") + glob.glob("/dev/cu.*")

        for port in portList:
            if "usb" in port.lower():
                returnList.append((port, port))

        return returnList

    ########################################
    # Menu Methods
    ########################################
    def toggleDebugging(self):
        if self.debug:
            indigo.server.log(u"Turning off debug logging")
            self.pluginPrefs["showDebugInfo"] = False
        else:
            indigo.server.log(u"Turning on debug logging")
            self.pluginPrefs["showDebugInfo"] = True

        self.debug = not self.debug

    def startInclusionMode(self):
        indigo.server.log(u"Turning on inclusion mode")

        self.inclusionMode = True

        self.interval = kWorkerSleep

        self.sendInternalCommand(kGatewayNodeId, kGatewayChildId, "INCLUSION_MODE", 1)

    def stopInclusionMode(self):
        indigo.server.log(u"Turning off inclusion mode")

        self.interval = kInterval

        self.inclusionMode = False

        self.sendInternalCommand(kGatewayNodeId, kGatewayChildId, "INCLUSION_MODE", 0)

    def reloadDevices(self):
        indigo.server.log(u"Reload devices")

        self.devices = indigo.Dict()
        self.nodeIds = indigo.Dict()

        self.setupNodeIds()

        self.pluginPrefs["devices"] = self.devices
        self.pluginPrefs["nodeIds"] = self.nodeIds

        self.loadDevices()
"""Device handler for Titan TPZRCO2TH-Z3 Environment Sensor."""
import logging

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice, CustomCluster
from zigpy.zcl.clusters.general import Basic, Identify, Ota, PollControl, PowerConfiguration
from zigpy.zcl.clusters.measurement import TemperatureMeasurement, RelativeHumidity

from zhaquirks import PowerConfigurationCluster
import zigpy.types as t

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

class GasConcentration(CustomCluster):
    cluster_id = 0x040D
    name = "Gas Concentration Measurement"
    ep_attribute = "gas_concentration"
    attributes = {
        0x0000: ("measured_value", t.Single),
        0x0001: ("min_measured_value", t.Single),
        0x0002: ("max_measured_value", t.Single),
        0xFFFD: ("cluster_revision", t.uint16_t),
    }
    server_commands = {}
    client_commands = {}

_LOGGER = logging.getLogger(__name__)

class TPZRCO2THZ3(CustomDevice):
    """Custom device representing Titan TPZRCO2TH-Z3 environment sensor."""

    signature = {
        MODELS_INFO: [("Titan Products Ltd", "TPZRCO2HT-Z3")],
        ENDPOINTS: {
        #  <SimpleDescriptor endpoint=1 profile=260 device_type=770
        #  device_version=1
        #  input_clusters=[0, 1, 3, 32, 1026, 1037]        
        #  output_clusters=[25]>
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,   
                INPUT_CLUSTERS: [
                    Basic.cluster_id,                    
                    PowerConfigurationCluster.cluster_id,  
                    Identify.cluster_id,                   
                    PollControl.cluster_id,                
                    TemperatureMeasurement.cluster_id,     
                    GasConcentration.cluster_id,                      
                ],
                OUTPUT_CLUSTERS: [Ota.cluster_id],         
            },
        #  <SimpleDescriptor endpoint=2 profile=260, device_type=775
        #  device_version=1
        #  input_clusters=[0, 1, 3, 1029]
        #  output_clusters=[]>
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.MINI_SPLIT_AC, 
                INPUT_CLUSTERS: [
                    Basic.cluster_id,                      
                    PowerConfigurationCluster.cluster_id,  
                    Identify.cluster_id,                   
                    RelativeHumidity.cluster_id,           
                ],
                OUTPUT_CLUSTERS: [],         
            }            
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,   
                INPUT_CLUSTERS: [
                    Basic.cluster_id,                    
                    PowerConfigurationCluster.cluster_id,  
                    Identify.cluster_id,                   
                    PollControl.cluster_id,                
                    TemperatureMeasurement.cluster_id,     
                    GasConcentration,                      
                ],
                OUTPUT_CLUSTERS: [Ota.cluster_id],      
            },
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.MINI_SPLIT_AC, 
                INPUT_CLUSTERS: [
                    Basic.cluster_id,                      
                    PowerConfigurationCluster.cluster_id,  
                    Identify.cluster_id,                   
                    RelativeHumidity.cluster_id,          
                ],
                OUTPUT_CLUSTERS: [],         
            }            
        },    
    }

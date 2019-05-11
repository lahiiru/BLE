using System;

namespace BeaconManager
{
    /// <summary>
    /// Holds the status data of a beacon node. Simply, this is the data structure for a beacon node
    /// IP address is the program level unique identifier
    /// </summary>
    class BeaconNode
    {
        // attributes of the node. 
        // always update according to the node's status update message
        // should not change in other places
        public string ipAddress;
        public int batteryLevel;
        public int upTimeMinutes;
        public string macAddress;
        public DateTime lastPing;
        public string status;
        public string id;
        // additional control variables
        public string tempId; // Holds newly created node ID. Until node picks it up.
        public bool fresh = true;
        public bool offline = false;

        public BeaconNode(string ipAddress)
        {
            this.ipAddress = ipAddress;
            this.lastPing = DateTime.Now;
            this.tempId = null;
        }

        public override bool Equals(object obj)
        {
            var node = obj as BeaconNode;
            return node != null &&
                   ipAddress == node.ipAddress;
        }

        public override int GetHashCode()
        {
            return ipAddress.GetHashCode();
        }
    }
}

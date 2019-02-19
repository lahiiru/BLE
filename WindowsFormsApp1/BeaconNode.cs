using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WindowsFormsApp1
{
    class BeaconNode
    {
        public string ipAddress;
        public int batteryLevel;
        public int upTimeMinutes;
        public DateTime lastPing;
        public string status;

        public BeaconNode(string ipAddress)
        {
            this.ipAddress = ipAddress;
            this.lastPing = DateTime.Now;
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

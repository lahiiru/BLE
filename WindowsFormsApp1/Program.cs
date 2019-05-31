using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace BeaconManager
{
    static class Program
    {
        static TcpListener listen;
        static Form1 form;
        public static Thread serverthread;
        public static UdpClient newsock = null;
        public static bool active = true;
        public static string log = "";
        public static readonly Dictionary<string, BeaconNode> nodes = new Dictionary<string, BeaconNode>();
        public static List<string> blockedIds = new List<string>();
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            Process ThisProcess = Process.GetCurrentProcess();
            Process[] AllProcesses = Process.GetProcessesByName(ThisProcess.ProcessName);
            if (AllProcesses.Length > 1)
            {
                // Exit silently if one instance fo the BeaconManager is already running.
                return;
            }
            
            serverthread = new Thread(new ThreadStart(DoListen)); // register UDP comminication handler thread
            serverthread.Start();

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            form = new Form1();
            Application.Run(form);
        }

        /// <summary>
        /// Listner thread's method
        /// </summary>
        private static void DoListen()
        {
            byte[] data = new byte[1024];
            IPEndPoint ipep = new IPEndPoint(IPAddress.Any, 9091); // start listnening on port
            newsock = new UdpClient(ipep);

            IPEndPoint sender = new IPEndPoint(IPAddress.Any, 0); // empty sender is needed as reference to catch senders information

            /*
                //TODO: New thread with client
                Thread clientThread = new Thread(new ParameterizedThreadStart(DoClient));
                clientThread.Start(client);
             */

            while (active)
            {
                Console.WriteLine("Waiting for a client...");
                data = newsock.Receive(ref sender); // here we wait until a message of node comes
                
                string port = sender.ToString(); // node's ip details
                string ip = port.Split(':')[0];
                Console.WriteLine("Connected {0}:", port);

                if (ip.Count(f => f == '.').Equals(3)) // if node does not provides a valid ip address do nothing 
                {
                    if (!nodes.ContainsKey(ip)) // if we don't have a node object for this ip
                    {
                        Console.WriteLine("Creating new node for {0}", ip);
                        nodes.Add(ip, new BeaconNode(ip)); // create new one and add to the node list
                    }
                    BeaconNode node = nodes[ip]; // take the relevant node from the list
                    ParseFrame(node, data); // ask to extract information from data buffer and update fields in node object
                
                    data = BuildManagementFrame(ip, node); // ask to build the response needs to be send to the given node
                    newsock.Send(data, data.Length, sender); // send server response
                }
            }
            
            newsock.Close();
        }

        public static bool HasReserved(string ip, string id) {
            foreach (string sid in Properties.Settings.Default.ids)
            {
                string[] data = sid.Split(':');
                string _ip = data[0];
                string _id = data[1];
                if (id.Equals(_id) && ip.Equals(_ip))
                {
                    return true;
                }
            }
            return false;
        }

        public static bool HasId(string ip, string id) {
            foreach(BeaconNode node in nodes.Values) {
                if (node.id == id) {
                    return true;
                }
            }
            foreach (string sid in Properties.Settings.Default.ids)
            {
                string[] data = sid.Split(':');
                string _ip = data[0];
                string _id = data[1];
                if (id.Equals(_id) && !ip.Equals(_ip))
                {
                    return true;
                }
            }
            foreach (string bid in blockedIds) {
                if (bid == id) {
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// Extract information from data buffer and update fields in node object
        /// </summary>
        /// <param name="node"></param>
        /// <param name="frame"></param>
        private static void ParseFrame(BeaconNode node, byte[] frame) {
            string stringFrame = Encoding.ASCII.GetString(frame, 0, frame.Length); // can use ASCII or UTF8
            Console.WriteLine(stringFrame);
            string[] tokens = stringFrame.Split('`'); // comming data seperated by :
            node.lastPing = DateTime.Now;
            node.offline = false;
            node.status = tokens[0];
            if ("pending-set".Equals(node.id) && node.tempId != tokens[1])
            {
                // still node haven't picked the given id.
            }
            else {
                if (("pending-set".Equals(node.id) || "not-set".Equals(node.id)) && node.tempId == tokens[1])
                {
                    // node just picked the given id
                    node.id = tokens[1];
                    string[] ids = new string[Properties.Settings.Default.ids.Count];
                    Properties.Settings.Default.ids.CopyTo(ids, 0);
                    foreach (string s in ids)
                    {
                        if (s.StartsWith(node.ipAddress))
                        {
                            Properties.Settings.Default.ids.Remove(s);
                        }
                    }
                    Properties.Settings.Default.ids.Add(node.ipAddress + ":" + node.id);
                    Properties.Settings.Default.Save();
                    blockedIds.RemoveAll(s => s == node.id);
                }
                else { // regular id update
                    node.id = tokens[1];
                    
                    if (!HasReserved(node.ipAddress, node.id))
                    {
                        if (Properties.Settings.Default.ids != null)
                        {
                            string[] ids = new string[Properties.Settings.Default.ids.Count];
                            Properties.Settings.Default.ids.CopyTo(ids, 0);
                            foreach (string s in ids) {
                                if (s.StartsWith(node.ipAddress)) {
                                    Properties.Settings.Default.ids.Remove(s);
                                }
                            }
                            Properties.Settings.Default.ids.Add(node.ipAddress + ":" + node.id);
                            Properties.Settings.Default.Save();
                        }
                    }
                }
            }
            node.upTimeMinutes = int.Parse(tokens[2]);
            node.batteryLevel = int.Parse(tokens[3]);
            node.macAddress = tokens[4];
            string data = tokens[5];
            log = DateTime.Now.ToLongTimeString() + ":  " + node.macAddress + " says it has discovered " + data + Environment.NewLine + log;
        }

        /// <summary>
        /// Build the response needs to be send to the given node
        /// </summary>
        /// <param name="ip"></param>
        /// <param name="node"></param>
        /// <returns></returns>
        private static byte[] BuildManagementFrame(string ip, BeaconNode node) {
            string managementFrame = "OK";
            if ("not-set".Equals(node.id) || "pending-set".Equals(node.id)) { // if client id is in not-set status, we need to tell an id
                if (node.tempId == null) {
                    node.tempId = Program.GetNewID(node.ipAddress).ToString();
                }
                managementFrame = "ID:" + node.tempId;
            }
            return Encoding.ASCII.GetBytes(managementFrame);
        }

        public static int GetNewID(string ip)
        {
            System.Collections.Specialized.StringCollection ids = Properties.Settings.Default.ids;
            if (ids == null) {
                ids = new System.Collections.Specialized.StringCollection();
                Properties.Settings.Default.ids = ids;
                Properties.Settings.Default.Save();
            }
            int id = 0;
            bool found = false;
            while (!found) {
                id++;
                found = true;
                foreach (string sid in ids)
                {
                    string[] data = sid.Split(':');
                    string _ip = data[0];
                    string _id = data[1];
                    if (id.ToString().Equals(_id) && !ip.Equals(_ip)) {
                        found = false;
                        break;
                    }
                }
                foreach (String sid in blockedIds)
                {
                    if (id.ToString().Equals(sid))
                    {
                        found = false;
                        break;
                    }
                }

            }
            blockedIds.Add(id.ToString());
            return id;
        }

    }

    // Implements the manual sorting of items by columns.
    class ListViewItemComparer : IComparer
    {
        private int col;
        public ListViewItemComparer()
        {
            col = 0;
        }
        public ListViewItemComparer(int column)
        {
            col = column;
        }
        public int Compare(object x, object y)
        {
            return String.Compare(((ListViewItem)y).SubItems[col].Text, ((ListViewItem)x).SubItems[col].Text);
        }
    }
}

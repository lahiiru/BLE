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
        public static Thread serverthread;
        public static bool active = true;
        public static readonly Dictionary<string, BeaconNode> nodes = new Dictionary<string, BeaconNode>();
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
            Application.Run(new Form1());
        }

        /// <summary>
        /// Listner thread's method
        /// </summary>
        private static void DoListen()
        {
            byte[] data = new byte[1024];
            IPEndPoint ipep = new IPEndPoint(IPAddress.Any, 9091); // start listnening on port
            UdpClient newsock = new UdpClient(ipep);

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

        /// <summary>
        /// Extract information from data buffer and update fields in node object
        /// </summary>
        /// <param name="node"></param>
        /// <param name="frame"></param>
        private static void ParseFrame(BeaconNode node, byte[] frame) {
            string stringFrame = Encoding.ASCII.GetString(frame, 0, frame.Length); // can use ASCII or UTF8
            Console.WriteLine(stringFrame);
            string[] tokens = stringFrame.Split(':'); // comming data seperated by :
            node.lastPing = DateTime.Now;
            node.status = tokens[0];
            node.id = tokens[1];
            node.upTimeMinutes = int.Parse(tokens[2]);
            node.batteryLevel = int.Parse(tokens[3]);
        }


        /// <summary>
        /// Build the response needs to be send to the given node
        /// </summary>
        /// <param name="ip"></param>
        /// <param name="node"></param>
        /// <returns></returns>
        private static byte[] BuildManagementFrame(string ip, BeaconNode node) {
            string managementFrame = "OK";
            if (node.id == "not-set") { // if client id is in not-set status, we need to tell an id
                managementFrame = "ID:" + node.tempId;
            }
            return Encoding.ASCII.GetBytes(managementFrame);
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

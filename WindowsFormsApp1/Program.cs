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

namespace WindowsFormsApp1
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
                //Don't put a MessageBox in here because the user could spam this MessageBox.
                return;
            }

            listen = new TcpListener(IPAddress.Parse("0.0.0.0"), 9091);
            serverthread = new Thread(new ThreadStart(DoListen));
            serverthread.Start();

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }


        private static void DoListen()
        {
            byte[] data = new byte[1024];
            IPEndPoint ipep = new IPEndPoint(IPAddress.Any, 9091);
            UdpClient newsock = new UdpClient(ipep);

            Console.WriteLine("Waiting for a client...");

            IPEndPoint sender = new IPEndPoint(IPAddress.Any, 0);
            /*
                //TODO: New thread with client
                Thread clientThread = new Thread(new ParameterizedThreadStart(DoClient));
                clientThread.Start(client);
             */

            while (active)
            {
                data = newsock.Receive(ref sender);
                string port = sender.ToString();
                string ip = port.Split(':')[0];
                Console.WriteLine("Connected {0}:", port);

                if (ip.Count(f => f == '.').Equals(3))
                {
                    if (!nodes.ContainsKey(ip))
                    {
                        Console.WriteLine("Creating new node for {0}", ip);
                        nodes.Add(ip, new BeaconNode(ip));
                    }
                    BeaconNode node = nodes[ip];
                    parseFrame(node, data);
                
                    data = BuildManagementFrame(ip);
                    newsock.Send(data, data.Length, sender);
                }
            }

            newsock.Close();
            listen.Stop();
          
        }

        private static void parseFrame(BeaconNode node, byte[] frame) {
            string stringFrame = Encoding.ASCII.GetString(frame, 0, frame.Length);
            Console.WriteLine(stringFrame);
            string[] tokens = stringFrame.Split(':');
            node.lastPing = DateTime.Now;
            node.status = tokens[0];
            node.upTimeMinutes = int.Parse(tokens[1]);
            node.batteryLevel = int.Parse(tokens[2]);
        }



        private static byte[] BuildManagementFrame(string ip) {
            string managementFrame = "OK";
            return Encoding.ASCII.GetBytes(managementFrame);
        }

        private static void DoClient(object client)
        {
            // Read data
            TcpClient tClient = (TcpClient)client;
            tClient.ReceiveBufferSize = 1024;

            Console.WriteLine("Client (Thread: {0}): Connected!", Thread.CurrentThread.ManagedThreadId);
            do
            {
                if (!tClient.Connected)
                {
                    Console.WriteLine("Killing thread (Thread: {0})", Thread.CurrentThread.ManagedThreadId);
                    tClient.Close();
                    Thread.CurrentThread.Abort();       // Kill thread.
                }

                if (tClient.Available > 0)
                {
                    // Reads NetworkStream into a byte buffer.
                    byte[] buffer = new byte[tClient.ReceiveBufferSize];

                    // Read can return anything from 0 to numBytesToRead.
                    // This method blocks until at least one byte is read.
                    int s = tClient.GetStream().Read(buffer, 0, (int)tClient.ReceiveBufferSize);
                    byte[] bytes = new byte[s];
                    Buffer.BlockCopy(buffer, 0, bytes, 0, s);
                    // Returns the data received from the host to the console.
                    string returndata = Encoding.UTF8.GetString(bytes);
                    // Resend
                    Console.WriteLine("Client (Thread: {0}): Data {1}", Thread.CurrentThread.ManagedThreadId, returndata);
                    tClient.GetStream().Write(bytes, 0, bytes.Length);
                }

                // Pause
                Thread.Sleep(100);
            } while (true);
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

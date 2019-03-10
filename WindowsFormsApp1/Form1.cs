using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Windows.Forms;

namespace BeaconManager
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Closed(object sender, EventArgs e)
        {
            Environment.Exit(1); // stop the application including running listner threads
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            string ip = FindIP(); // 
            if (ip == null) {
                MessageBox.Show("Connect to a WIFI access point first.", "No connect WIFI interface found.", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            label2.Text = ip;
        }

        /// <summary>
        /// Find IP address of WIFI interface by iteration over all interfaces. 
        /// This IP should be a static one and need to be added to the python script in nodes
        /// </summary>
        /// <returns></returns>
        private string FindIP() {
            foreach (NetworkInterface ni in NetworkInterface.GetAllNetworkInterfaces())
            {
                if (ni.NetworkInterfaceType == NetworkInterfaceType.Wireless80211 && ni.OperationalStatus == OperationalStatus.Up)
                {
                    Console.WriteLine(ni.Name);
                    foreach (UnicastIPAddressInformation ip in ni.GetIPProperties().UnicastAddresses)
                    {
                        if (ip.Address.AddressFamily == AddressFamily.InterNetwork)
                        {
                            return ip.Address.ToString();
                        }
                    }
                }
            }
            return null;
        }

        // ColumnClick event handler.
        private void SortColumnClick(object o, ColumnClickEventArgs e)
        {
            // Set the ListViewItemSorter property to a new ListViewItemComparer 
            // object. Setting this property immediately sorts the 
            // ListView using the ListViewItemComparer object.
            listView1.ListViewItemSorter = new ListViewItemComparer(e.Column);
        }

        private void listView1_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        public TextBox LogBox
        {
            get { return textBox1; }
        }

        public void Log()
        {
            textBox1.Text = Program.log;
        }

        /// <summary>
        /// Repeatedly update to List View with <code>Program.nodes</code>
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void Timer1_Tick(object sender, EventArgs e)
        {
            Log();
            label1.Text = DateTime.Now.ToLongTimeString();
            listView1.BeginUpdate(); // Tell GUI to catch the update
            foreach (KeyValuePair<string, BeaconNode> node in Program.nodes.OrderBy(i => i.Value.lastPing))
            {
                if (!listView1.Items.ContainsKey(node.Value.ipAddress)) // Add if it not in the list view
                {
                    ListViewItem lv = new ListViewItem(node.Value.id); // initiate with 1st column value
                    lv.Name = node.Value.ipAddress; // set the identifier of the list view item. it's ip
                    lv.SubItems.Add(node.Value.ipAddress); // set 2nd column values
                    lv.SubItems.Add(node.Value.macAddress);
                    lv.SubItems.Add(node.Value.lastPing.ToString()); // 4th column values
                    lv.SubItems.Add(node.Value.upTimeMinutes.ToString());
                    lv.SubItems.Add(node.Value.batteryLevel.ToString());
                    listView1.Items.Add(lv);
                }
                else { // update if already in the list view
                    ListViewItem lv = listView1.Items.Find(node.Value.ipAddress, false)[0];
                    lv.SubItems[0].Text = node.Value.id;
                    lv.SubItems[1].Text = node.Value.ipAddress;
                    lv.SubItems[2].Text = node.Value.macAddress;
                    lv.SubItems[3].Text = node.Value.lastPing.ToString();
                    lv.SubItems[4].Text = node.Value.upTimeMinutes.ToString();
                    lv.SubItems[5].Text = node.Value.batteryLevel.ToString();
                }
            }
            listView1.EndUpdate();
        }
    }
}

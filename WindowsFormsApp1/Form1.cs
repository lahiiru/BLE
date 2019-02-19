using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Windows.Forms;

namespace WindowsFormsApp1
{
    public partial class Form1 : Form
    {


        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Closed(object sender, EventArgs e)
        {
            Program.active = false;
            Environment.Exit(1);
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            string ip = findIP();
            if (ip == null) {
                MessageBox.Show("Connect to a WIFI access point first.", "No connect WIFI interface found.", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            label2.Text = ip;
        }

        private string findIP() {
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

        private void timer1_Tick(object sender, EventArgs e)
        {
            label1.Text = DateTime.Now.ToLongTimeString();
            listView1.BeginUpdate();
            foreach (KeyValuePair<string, BeaconNode> node in Program.nodes.OrderBy(i => i.Value.lastPing))
            {
                if (!listView1.Items.ContainsKey(node.Value.ipAddress))
                {
                    ListViewItem lv = new ListViewItem(node.Value.id);
                    lv.Name = node.Value.ipAddress;
                    lv.SubItems.Add(node.Value.ipAddress);
                    lv.SubItems.Add(node.Value.lastPing.ToString());
                    lv.SubItems.Add(node.Value.upTimeMinutes.ToString());
                    lv.SubItems.Add(node.Value.batteryLevel.ToString());
                    listView1.Items.Add(lv);
                }
                else {
                    ListViewItem lv = listView1.Items.Find(node.Value.ipAddress, false)[0];
                    lv.SubItems[0].Text = node.Value.id;
                    lv.SubItems[1].Text = node.Value.ipAddress;
                    lv.SubItems[2].Text = node.Value.lastPing.ToString();
                    lv.SubItems[3].Text = node.Value.upTimeMinutes.ToString();
                    lv.SubItems[4].Text = node.Value.batteryLevel.ToString();
                }
            }
            listView1.EndUpdate();
        }
    }
}

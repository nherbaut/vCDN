sudo ovs-ofctl del-flows s11
sudo ovs-ofctl add-flow s11 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s11 ip,nw_dst=10.0.0.1,actions=output:1
sudo ovs-ofctl add-flow s11 ip,nw_dst=10.0.0.2,actions=output:2
sudo ovs-ofctl add-flow s11 ip,nw_dst=10.0.0.5,actions=output:3



sudo ovs-ofctl del-flows s12
sudo ovs-ofctl add-flow s12 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s12 ip,nw_dst=10.0.0.2,actions=output:1
sudo ovs-ofctl add-flow s12 ip,nw_dst=10.0.0.1,actions=output:2

sudo ovs-ofctl del-flows s21
sudo ovs-ofctl add-flow s21 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s21 ip,nw_dst=10.0.0.3,actions=output:1
sudo ovs-ofctl add-flow s21 ip,nw_dst=10.0.0.5,actions=output:4
sudo ovs-ofctl add-flow s21 ip,nw_dst=10.0.0.1,actions=output:2

sudo ovs-ofctl del-flows s22
sudo ovs-ofctl add-flow s22 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s22 ip,nw_dst=10.0.0.4,actions=output:1
sudo ovs-ofctl add-flow s22 ip,nw_dst=10.0.0.1,actions=output:1

sudo ovs-ofctl del-flows s31
sudo ovs-ofctl add-flow s31 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s31 ip,nw_dst=10.0.0.5,actions=output:1
sudo ovs-ofctl add-flow s31 ip,nw_dst=10.0.0.1,actions=output:2

sudo ovs-ofctl del-flows s32
sudo ovs-ofctl add-flow s32 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s32 ip,nw_dst=10.0.0.6,actions=output:1

sudo ovs-ofctl del-flows s41
sudo ovs-ofctl add-flow s41 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s41 ip,nw_dst=10.0.0.7,actions=output:1

sudo ovs-ofctl del-flows s42
sudo ovs-ofctl add-flow s42 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s42 ip,nw_dst=10.0.0.8,actions=output:1

sudo ovs-ofctl del-flows s51
sudo ovs-ofctl add-flow s51 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s51 ip,nw_dst=10.0.0.9,actions=output:1

sudo ovs-ofctl del-flows s52
sudo ovs-ofctl add-flow s52 arp,icmp,actions=normal
sudo ovs-ofctl add-flow s52 ip,nw_dst=10.0.0.10,actions=output:1

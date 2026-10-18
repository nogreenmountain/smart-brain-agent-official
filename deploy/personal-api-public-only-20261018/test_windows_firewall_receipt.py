import unittest
from windows_firewall_receipt import exact_ipv4_filter

class FirewallReceiptTest(unittest.TestCase):
    def test_accepts_equivalent_single_host_renderings(self):
        for value in ['192.168.10.165','192.168.10.165/32','192.168.10.165-192.168.10.165']:
            with self.subTest(value=value):
                self.assertTrue(exact_ipv4_filter(value,'192.168.10.165'))
    def test_rejects_widened_or_wrong_filters(self):
        for value in ['Any','192.168.10.0/24','192.168.10.164-192.168.10.165','192.168.10.165-192.168.10.166','192.168.10.165,192.168.10.166','192.168.10.164','::ffff:192.168.10.165','']:
            with self.subTest(value=value):
                self.assertFalse(exact_ipv4_filter(value,'192.168.10.165'))

if __name__=='__main__':unittest.main()

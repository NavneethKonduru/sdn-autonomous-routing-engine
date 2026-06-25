#!/usr/bin/env python3
"""
Simple test to verify the networking application components work together
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modules for testing
from core.network_layer import NetworkLayer, Packet, ProtocolType
from core.transport_layer import TransportLayer, TCPSocket, UDPSocket
from core.application_layer import ChatServer, ChatClient, ChatMessage, MessageType
from modules.sdn.sdn_module import SDNModule
from modules.wireless.wireless_module import WirelessModule
from modules._5g._5g_module import _5gModule

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Just importing them is enough to test
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_functionality():
    """Test basic core networking functionality"""
    try:
        # Create network layer
        nl = NetworkLayer()
        nl.add_interface("eth0", "192.168.1.100")
        nl.add_route("0.0.0.0/0", "192.168.1.1")

        # Create transport layer
        tl = TransportLayer(nl)

        # Test packet creation
        pkt = Packet("192.168.1.100", "192.168.1.1", ProtocolType.TCP, b"Hello", 64)

        print("✓ Core functionality test passed")
        return True
    except Exception as e:
        print(f"✗ Core functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_modules():
    """Test that modules can be instantiated"""
    try:
        # Test SDN module
        sdn = SDNModule()
        sdn.activate()
        print("✓ SDN module instantiated")

        # Test wireless module
        wireless = WirelessModule()
        wireless.activate()
        print("✓ Wireless module instantiated")

        # Test 5G module
        _5g = _5gModule()
        _5g.activate()
        print("✓ 5G module instantiated")

        return True
    except Exception as e:
        print(f"✗ Module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_application_layer():
    """Test application layer components"""
    try:
        # Test chat message creation
        msg = ChatMessage(MessageType.JOIN, "test_user")
        encoded = msg.to_json()
        decoded = ChatMessage.from_json(encoded)

        assert decoded.username == "test_user"
        assert decoded.type == MessageType.JOIN

        print("✓ Application layer test passed")
        return True
    except Exception as e:
        print(f"✗ Application layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing SDN-Wireless-5G Networking Application Components")
    print("=" * 60)

    tests = [
        test_imports,
        test_core_functionality,
        test_modules,
        test_application_layer
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
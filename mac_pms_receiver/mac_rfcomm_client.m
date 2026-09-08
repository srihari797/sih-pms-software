/*
 * Native macOS Bluetooth Classic RFCOMM Client for PMS (Patient Monitoring System)
 * 
 * Uses Apple's native IOBluetooth framework.
 * Connects to Windows PMS Laptop Bluetooth MAC address and RFCOMM channel.
 * Flushes raw incoming byte stream directly to stdout for line-delimited JSON parsing.
 *
 * Compilation on macOS:
 *   clang -O2 -framework IOBluetooth -framework Foundation mac_rfcomm_client.m -o mac_rfcomm_client
 *
 * Usage:
 *   ./mac_rfcomm_client <MAC_ADDRESS> <CHANNEL>
 *   Example: ./mac_rfcomm_client C0:35:32:26:20:18 5
 */

#import <Foundation/Foundation.h>
#import <IOBluetooth/IOBluetooth.h>
#include <stdio.h>
#include <signal.h>

static BOOL g_running = YES;

void signalHandler(int sig) {
    g_running = NO;
    CFRunLoopStop(CFRunLoopGetCurrent());
}

@interface RFCOMMDelegate : NSObject <IOBluetoothRFCOMMChannelDelegate>
@property (nonatomic, assign) BOOL connected;
@end

@implementation RFCOMMDelegate

- (void)rfcommChannelData:(IOBluetoothRFCOMMChannel *)rfcommChannel data:(void *)dataPointer length:(size_t)dataLength {
    if (dataPointer && dataLength > 0) {
        fwrite(dataPointer, 1, dataLength, stdout);
        fflush(stdout);
    }
}

- (void)rfcommChannelOpenComplete:(IOBluetoothRFCOMMChannel *)rfcommChannel status:(IOReturn)error {
    if (error == kIOReturnSuccess) {
        self.connected = YES;
        fprintf(stderr, "[MAC RFCOMM] >>> CONNECTED TO PMS VIA NATIVE MACOS IOBLUETOOTH RFCOMM!\n");
    } else {
        self.connected = NO;
        fprintf(stderr, "[MAC RFCOMM] Open RFCOMM channel failed with status: 0x%x\n", error);
        CFRunLoopStop(CFRunLoopGetCurrent());
    }
}

- (void)rfcommChannelClosed:(IOBluetoothRFCOMMChannel *)rfcommChannel {
    self.connected = NO;
    fprintf(stderr, "\n[MAC RFCOMM] [WARNING] RFCOMM channel closed by remote host.\n");
    CFRunLoopStop(CFRunLoopGetCurrent());
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        signal(SIGINT, signalHandler);
        signal(SIGTERM, signalHandler);

        if (argc < 3) {
            fprintf(stderr, "Usage: mac_rfcomm_client <MAC_ADDRESS> <CHANNEL>\n");
            fprintf(stderr, "Example: mac_rfcomm_client C0:35:32:26:20:18 5\n");
            return 1;
        }

        NSString *macStr = [NSString stringWithUTF8String:argv[1]];
        BluetoothRFCOMMChannelID channelID = (BluetoothRFCOMMChannelID)atoi(argv[2]);

        // Normalize MAC address format (replace ':' with '-')
        NSString *formattedMAC = [macStr stringByReplacingOccurrencesOfString:@":" withString:@"-"];
        
        fprintf(stderr, "[MAC RFCOMM] Connecting to PMS Bluetooth MAC=%s CHANNEL=%d...\n", [formattedMAC UTF8String], channelID);

        IOBluetoothDevice *device = [IOBluetoothDevice deviceWithAddressString:formattedMAC];
        if (!device) {
            fprintf(stderr, "[MAC RFCOMM] ERROR: Could not find paired Bluetooth device for MAC: %s\n", [formattedMAC UTF8String]);
            return 1;
        }

        RFCOMMDelegate *delegate = [[RFCOMMDelegate alloc] init];
        IOBluetoothRFCOMMChannel *rfcommChannel = nil;

        IOReturn status = [device openRFCOMMChannelSync:&rfcommChannel withChannelID:channelID delegate:delegate];
        if (status != kIOReturnSuccess || !rfcommChannel) {
            fprintf(stderr, "[MAC RFCOMM] Failed to open RFCOMM channel sync: 0x%x\n", status);
            return 1;
        }

        // Run loop to process asynchronous RFCOMM events and data callbacks
        while (g_running && [delegate connected]) {
            [[NSRunLoop currentRunLoop] runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.5]];
        }

        if (rfcommChannel) {
            [rfcommChannel closeChannel];
        }
    }
    return 0;
}

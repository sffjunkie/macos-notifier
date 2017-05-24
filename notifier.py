import objc
import Cocoa

NSApplicationDelegate = objc.protocolNamed('NSApplicationDelegate')
NSUserNotificationCenterDelegate = objc.protocolNamed('NSUserNotificationCenterDelegate')

TerminalNotifierBundleID = "uk.co.sffjunkie.terminal-notifier"
NotificationCenterUIBundleID = "com.apple.notificationcenterui"

_fakeBundleIdentifier = None

class AppDelegate(NSObject, protocols=[NSApplicationDelegate, NSUserNotificationCenterDelegate]):
    def __init__(self):
        self._fake_bundle_identifier = None
        self._current_notification = None

    def __bundleIdentifier(self):
        if self is Cocoa.nsBundle.mainBundle():
            return self._fake_bundle_identifier or TerminalNotifierBundleID
        else:
            return self.__bundleIdentifier


    def bye_(self):
        uuid = self._current_notification.userInfo["uuid"]
        notification_center = NSUserNotificationCenter.defaultUserNotificationCenter
        for nox in notification_center.deliveredNotifications:
            if nox.userInfo['uuid'] == uuid:
                notification_center.removeDeliveredNotification_(nox)

    def initializeUserDefaults_():
        defaults = NSUserDefaults.standardUserDefaults_()
        app_defaults = {'sender', 'com.apple.Terminal'}
        defaults.registerDefaults_(app_defaults)

    def printHelpBanner_(self):
        pass

    def applicationDidFinishLaunching_(self, notification):
        pass


def InstallFakeBundleIdentifierHook():
    cl = objc.getClass('NSBundle')
    if cl:
        cl.bundleIdentifier = self.__bundleIdentifier
        return True
    else:
        return False

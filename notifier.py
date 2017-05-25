import AppKit
import Cocoa
import objc
import os
import sys
from urllib.parse import urlparse

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

    def objectForKeyedSubscript_key_(self, key):
        obj = self[key]
        if isinstance(obj, str) and obj[0] == '\\':
            obj = obj[1:]
        return obj

    def initializeUserDefaults_():
        defaults = AppKit.NSUserDefaults.standardUserDefaults()
        app_defaults = {'sender', 'com.apple.Terminal'}
        defaults.registerDefaults(app_defaults)

    def printHelpBanner_(self):
        pass

    def applicationDidFinishLaunching_(self, notification):
        userNotification = notification.userInfo['NSApplicationLaunchUserNotificationKey']
        if userNotification:
            self.userActivatedNotification_(userNotification)
        else:
            if '-help' in sys.argv:
                self.printHelpBanner_()
                sys.exit(0)

        if NotificationCenterUIBundleID not in AppKit.NSWorkspace.sharedWorkspace().runningApplications():
            print("[!] Unable to post a notification for the current user (%s), as it has no running NotificationCenter instance.", AppKit.NSUserName())
            sys.exit(1)

        defaults = AppKit.NSUserDefaults.standardUserDefaults()

        subtitle = defaults.get("subtitle", None)
        message  = defaults.get("message", None)
        remove_  = defaults.get("remove", None)
        list_    = defaults.get("list", None)
        sound    = defaults.get("sound", None)

        if not message and not os.isatty(os.STDIN_FILENO):
            data = []
            with open(os.STDIN_FILENO) as fp:
                while True:
                    d = fp.read(-1)
                    if d:
                        data.append(d)
                    else:
                        break

            message = ''.join(data)
            message = message.decode('UTF-8')

        if message is None and remove_ is None and list_ is None:
            self.printHelpBanner_()
            sys.exit(1)

        if list_:
            self.listNotificationWithGroupID_(list_)
            sys.exit(0)

        if 'sender' in defaults:
            if InstallFakeBundleIdentifierHook():
                _fakeBundleIdentifier = defaults['sender'];

        if remove_:
            self.removeNotificationWithGroupID_(remove_)
            if not message
                sys.exit(0)

        if message:
            options = {}
            if 'activate' in defaults:
                options['bundleID'] = defaults['activate']

            if 'group' in defaults:
                options['groupID'] = defaults['group']

            if 'execute' in defaults:
                options['command'] = defaults['execute']

            if 'appIcon' in defaults:
                options['appIcon'] = defaults['appIcon']

            if 'contentImage' in defaults:
                options['contentImage'] = defaults['contentImage']

            if 'closeLabel' in defaults:
                options['closeLabel'] = defaults['closeLabel']

            if 'dropdownLabel' in defaults:
                options['dropdownLabel'] = defaults['dropdownLabel']

            if 'actions' in defaults:
                options['actions'] = defaults['actions']

            if '-reply' in sys.argv:
                if 'reply' in defaults:
                    options['reply'] = defaults['reply']
                else:
                    options['reply'] = 'Reply'

            if '-json' in sys.agv:
                options['output'] = 'json'
            else:
                options['output'] = 'outputEvent'

            options['uuid'] = id(self)
            options['timeout'] = defaults.get('timeout', 0)

            if options[@"reply"] or defaults["timeout"] or defaults["actions"] or defaults["execute"] or defaults["open"] or options["bundleID"]:
                options["waitForResponse"] = objc.YES

            if defaults['open']:
                info = urlparse(defaults['open'])
                if info and info.scheme and info.netloc:
                    options['open'] = defaults['open']
                else:
                    print("'%s' is not a valid URI.", defaults["open"])
                    sys.exit(1)

            title = defaults.get('title', 'Terminal')
            self.deliverNotificationWithTitle(title,
                                              subtitle,
                                              message,
                                              options,
                                              sound)

    def getImageFromURL_(self, url):
        pass

    def deliverNotificationWithTitle_subtitle_message_options_sound_(self, title, subtitle, message, options, sound):
        if options['groupID']:
            self.removeNotificationWithGroupID(options['groupID'])

        notification = AppKit.NSUserNotification()
        notification.title = title
        notification.subtitle = subtitle
        notification.informativeText = message
        notification.userInfo = options

        if 'appIcon' in options:
            notification['_identityImage'] = self.getImageFromURL_(options['appIcon'])
            notification['_identityImageHasBorder'] = objc.False

        if 'contentImage' in options:
            notification.contentImage = self.getImageFromURL_(options['contentImage'])

        if 'actions' in options:
            notification._showsButtons = objc.YES
            myActions = options['actions'].split(',')
            if len(myActions) > 1:
                notification._alwaysShowAlternateActionMenu = objc.YES
                notification._alternateActionButtonTitles = myActions

                if 'dropdownLabel' in options:
                    notification.actionButtonTitle = options['dropdownLabel']
                    notification.hasActionButton = True
            else:
                notification.actionButtonTitle = myActions
        elif 'reply' in options:
            notification._showsButtons = objc.YES
            notification.hasReplyButton = 1
            notification.responsePlaceholder = options['reply']

        if 'closeLabel' in options:
            notification.otherButtonTitle = options['closeLabel']

        if sound:
            notification.soundName = sound == 'default' ? AppKit.NSUserNotificationDefaultSoundName : sound

        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.delegate = self
        center.deliverNotification(notification)

    def removeNotificationWithGroupID_(self, groupID):
        center = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
        for notification in center.deliveredNotifications():
            if groupID == 'ALL' or notification.userInfo["groupID"] == groupID:
                center.removeDeliveredNotification(notification)

    def userActivatedNotification_(self, userNotification):
        center = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
        center.removeDeliveredNotification(userNotification)

        groupID  = userNotification.userInfo["groupID"]
        bundleID = userNotification.userInfo["bundleID"]
        command  = userNotification.userInfo["command"]
        open_     = userNotification.userInfo["open"]

        if bundleID:
            self.activateAppWithBundleID(bundleID)

        if command:
                self.executeShellCommand(command)

        #if open_:
        #    AppKit.NSWorkspace.sharedWorkspace().openURL:[NSURL URLWithString:open]];

    def activateAppWithBundleID_(self, bundleID):
        app = AppKit.SBApplication.applicationWithBundleIdentifier(bundleID)
        if app:
            app.activate()
            return objc.YES
        else:
            print("Unable to find an application with the specified bundle indentifier.")
            return objc.NO

    # TODO
    def executeShellCommand_(self, command):
        pass

    def userNotificationCenter_shouldPresentNotification_(self, center, notification):
        return objc.YES

    def userNotificationCenter_didDeliverNotification_(self, center, userNotification):
        if userNotification.userInfo.get("waitForResponse", False):
            return

    def userNotificationCenter_didActivateNotification_(self, center, notification):
        if notification.userInfo['uuid'] != str(id(self)):
            return

        additionalActionIndex = -1L

        if notification.activationType == NSUserNotificationActivationTypeAdditionalActionClicked or
            notification.activationType == NSUserNotificationActivationTypeActionButtonClicked:

            if len(notification._alternateActionButtonTitles) > 1:
                alternateActionIndex = notification._alternateActionIndex
                additionalActionIndex = int(alternateActionIndex)

                ActionsClicked = notification._alternateActionButtonTitles[additionalActionIndex]


    def listNotificationWithGroupID_(self, listGroupID):
        pass

    def Quit(self, udict, notification):
        pass

    def bye_(self):
        uuid = self._current_notification.userInfo["uuid"]
        notification_center = NSUserNotificationCenter.defaultUserNotificationCenter
        for nox in notification_center.deliveredNotifications:
            if nox.userInfo['uuid'] == uuid:
                notification_center.removeDeliveredNotification_(nox)


def InstallFakeBundleIdentifierHook():
    cl = objc.getClass('NSBundle')
    if cl:
        cl.bundleIdentifier = self.__bundleIdentifier
        return True
    else:
        return False

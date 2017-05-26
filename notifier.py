import AppKit
import Cocoa
import Foundation
import objc
import os
import sys
from urllib.parse import urlparse

NSApplicationDelegate = objc.protocolNamed('NSApplicationDelegate')
NSUserNotificationCenterDelegate = objc.protocolNamed('NSUserNotificationCenterDelegate')

TerminalNotifierBundleID = "uk.co.sffjunkie.terminal-notifier"
NotificationCenterUIBundleID = "com.apple.notificationcenterui"


class AppDelegate(AppKit.NSObject, protocols=[NSApplicationDelegate, NSUserNotificationCenterDelegate]):
    def __init__(self):
        self._fake_bundle_identifier = None
        self._current_notification = None

    def __bundleIdentifier(self):
        if self is Cocoa.NSBundle.mainBundle():
            return self._fake_bundle_identifier or TerminalNotifierBundleID
        else:
            return self.__bundleIdentifier

    def objectForKeyedSubscript_(self, key):
        obj = self[key]
        if isinstance(obj, str) and obj[0] == '\\':
            obj = obj[1:]
        return obj

    def initializeUserDefaults(self):
        defaults = AppKit.NSUserDefaults.standardUserDefaults()
        app_defaults = {'sender', 'com.apple.Terminal'}
        defaults.registerDefaults_(app_defaults)

    def printHelpBanner(self):
        appName = sys.argv[0]
        appVersion = '0.1alpha'
        print("""%s (%s) is a command-line tool to send OS X User Notifications.

        Usage: %s -[message|list|remove] [VALUE|ID|ID] [options]

           Either of these is required (unless message data is piped to the tool):

               -help              Display this help banner.
               -version           Display terminal-notifier version.
               -message VALUE     The notification message.
               -remove ID         Removes a notification with the specified ‘group’ ID.
               -list ID           If the specified ‘group’ ID exists show when it was delivered,
                                  or use ‘ALL’ as ID to see all notifications.
                                  The output is a tab-separated list.

           Reply type notification:

               -reply VALUE       The notification will be displayed as a reply type alert, VALUE used as placeholder.

           Actions type notification:

               -actions VALUE1,VALUE2.
                                  The notification actions avalaible.
                                  When you provide more than one value, a dropdown will be displayed.
                                  You can customize this dropdown label with the next option.
               -dropdownLabel VALUE
                                  The notification actions dropdown title (only when multiples actions are provided).
                                  Notification style must be set to Alert.

           Optional:

               -title VALUE       The notification title. Defaults to ‘Terminal’.
               -subtitle VALUE    The notification subtitle.
               -closeLabel VALUE  The notification close button label.
               -sound NAME        The name of a sound to play when the notification appears. The names are listed
                                  in Sound Preferences. Use 'default' for the default notification sound.
               -group ID          A string which identifies the group the notifications belong to.
                                  Old notifications with the same ID will be removed.
               -activate ID       The bundle identifier of the application to activate when the user clicks the notification.
               -sender ID         The bundle identifier of the application that should be shown as the sender, including its icon.
               -appIcon URL       The URL of a image to display instead of the application icon.
               -contentImage URL  The URL of a image to display attached to the notification.
               -open URL          The URL of a resource to open when the user clicks the notification.
               -execute COMMAND   A shell command to perform when the user clicks the notification.
               -timeout NUMBER    Close the notification after NUMBER seconds.
               -json              Output event or value to stdout as JSON.

        When the user activates a notification, the results are logged to the system logs.
        Use Console.app to view these logs.

        Note that in some circumstances the first character of a message has to be escaped in order to be recognized.
        An example of this is when using an open bracket, which has to be escaped like so: ‘\\[’.

        For more information see https://github.com/julienXX/terminal-notifier.""" % (appName, appVersion, appName))

    def applicationDidFinishLaunching_(self, notification):
        if '-help' in sys.argv:
            self.printHelpBanner()
            AppKit.NSApp().terminate_(self)
            sys.exit(0)

        userNotification = notification.userInfo().get('NSApplicationLaunchUserNotificationKey', None)
        if userNotification:
            self.userActivatedNotification_(userNotification)

        bundles = [app.bundleIdentifier() for app in AppKit.NSWorkspace.sharedWorkspace().runningApplications()]
        if NotificationCenterUIBundleID not in bundles:
            print("[!] Unable to post a notification for the current user (%s), as it has no running NotificationCenter instance.", AppKit.NSUserName())
            sys.exit(1)

        defaults = AppKit.NSUserDefaults.standardUserDefaults()

        subtitle = defaults.get("subtitle", None)
        message  = defaults.get("message", None)
        remove_  = defaults.get("remove", None)
        list_    = defaults.get("list", None)
        sound    = defaults.get("sound", None)

        if not message and not os.isatty(sys.stdin.fileno()):
            data = []
            with open(sys.stdin.fileno()) as fp:
                while True:
                    d = fp.read(-1)
                    if d:
                        data.append(d)
                    else:
                        break

            message = ''.join(data)
            message = message.decode('UTF-8')

        if message is None and remove_ is None and list_ is None:
            self.printHelpBanner()
            AppKit.NSApp().terminate_(self)
            sys.exit(1)

        if list_:
            self.listNotificationWithGroupID_(list_)
            AppKit.NSApp().terminate_(self)
            sys.exit(0)

        if 'sender' in defaults:
            if InstallFakeBundleIdentifierHook():
                self._fakeBundleIdentifier = defaults['sender'];

        if remove_:
            self.removeNotificationWithGroupID_(remove_)
            if not message:
                AppKit.NSApp().terminate_(self)
                sys.exit(0)

        if message:
            options = objc.lookUpClass("NSMutableDictionary").alloc().init()
            if 'activate' in defaults:
                options.setValue_forKey_('bundleID', defaults['activate'])

            if 'group' in defaults:
                options.setValue_forKey_('groupID', defaults['group'])

            if 'execute' in defaults:
                options.setValue_forKey_('command', defaults['execute'])

            if 'appIcon' in defaults:
                options.setValue_forKey_('appIcon', defaults['appIcon'])

            if 'contentImage' in defaults:
                options.setValue_forKey_('contentImage', defaults['contentImage'])

            if 'closeLabel' in defaults:
                options.setValue_forKey_('closeLabel', defaults['closeLabel'])

            if 'dropdownLabel' in defaults:
                options.setValue_forKey_('dropdownLabel', defaults['dropdownLabel'])

            if 'actions' in defaults:
                options.setValue_forKey_('actions', defaults['actions'])

            if '-reply' in sys.argv:
                if 'reply' in defaults:
                    options.setValue_forKey_('reply', defaults['reply'])
                else:
                    options.setValue_forKey_('reply', 'Reply')
            #
            # if '-json' in sys.argv:
            #     options.setValue_forKey_('output', 'json')
            # else:
            #     options.setValue_forKey_('output', 'outputEvent')
            #
            # options.setValue_forKey_('uuid', str(id(self)).encode('ASCII'))
            # options.setValue_forKey_('timeout', defaults.get('timeout', 0))
            #
            # if "reply" in options or "timeout" in defaults or "actions" in defaults or \
            #     "execute" in defaults or "open" in defaults or "bundleID" in options:
            #     options.setValue_forKey_("waitForResponse", objc.YES)
            #
            # if 'open' in defaults:
            #     info = urlparse(defaults['open'])
            #     if info and info.scheme and info.netloc:
            #         options.setValue_forKey_('open', defaults['open'])
            #     else:
            #         print("'%s' is not a valid URI.", defaults["open"])
            #         sys.exit(1)

            title = defaults.get('title', 'Terminal')
            self.deliverNotificationWithTitle_subtitle_message_options_sound_(title,
                                              subtitle,
                                              message,
                                              options,
                                              sound)

    def getImageFromURL_(self, url):
        pass

    def deliverNotificationWithTitle_subtitle_message_options_sound_(self, title, subtitle, message, options, sound):
        if 'groupID' in options:
            self.removeNotificationWithGroupID(options['groupID'])

        notification = AppKit.NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setSubtitle_(subtitle)
        notification.setInformativeText_(message)
        notification.setUserInfo_(options)
        # print(dir(notification))

        # if 'appIcon' in options:
        #     notification.setValue_forKey_('_identityImage', self.getImageFromURL_(options['appIcon']))
        #     notification.setValue_forKey_('_identityImageHasBorder', False)
        #
        # if 'contentImage' in options:
        #     notification.setValue_forKey_('contentImage', self.getImageFromURL_(options['contentImage']))
        #
        # if 'actions' in options:
        #     notification._showsButtons = objc.YES
        #     myActions = options['actions'].split(',')
        #     if len(myActions) > 1:
        #         notification._alwaysShowAlternateActionMenu = objc.YES
        #         notification._alternateActionButtonTitles = myActions
        #
        #         if 'dropdownLabel' in options:
        #             notification.actionButtonTitle = options['dropdownLabel']
        #             notification.hasActionButton = True
        #     else:
        #         notification.actionButtonTitle = myActions
        # elif 'reply' in options:
        #     notification._showsButtons = objc.YES
        #     notification.hasReplyButton = 1
        #     notification.responsePlaceholder = options['reply']
        #
        # if 'closeLabel' in options:
        #     notification.otherButtonTitle = options['closeLabel']
        #
        if sound:
            if sound == 'default':
                notification.soundName = AppKit.NSUserNotificationDefaultSoundName
            else:
                notification.soundName = sound

        center = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
        center.setDelegate_(self)
        center.deliverNotification_(notification)

    def removeNotificationWithGroupID_(self, groupID):
        center = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
        # for notification in center.deliveredNotifications():
        #     if groupID == 'ALL' or notification.userInfo["groupID"] == groupID:
        #         center.removeDeliveredNotification(notification)

    def userActivatedNotification_(self, userNotification):
        center = AppKit.NSUserNotificationCenter.defaultUserNotificationCenter()
        center.removeDeliveredNotification_(userNotification)
        #
        # groupID = userNotification.userInfo["groupID"]
        # bundleID = userNotification.userInfo["bundleID"]
        # command = userNotification.userInfo["command"]
        # open_ = userNotification.userInfo["open"]
        #
        # if bundleID:
        #     self.activateAppWithBundleID(bundleID)
        #
        # if command:
        #         self.executeShellCommand(command)
        #
        #if open_:
        #    AppKit.NSWorkspace.sharedWorkspace().openURL:[NSURL URLWithString:open]];

    def activateAppWithBundleID_(self, bundleID):
        app = AppKit.SBApplication.applicationWithBundleIdentifier(bundleID)
        # if app:
        #     app.activate()
        #     return objc.YES
        # else:
        #     print("Unable to find an application with the specified bundle indentifier.")
        #     return objc.NO

    # TODO
    def executeShellCommand_(self, command):
        pass

    def userNotificationCenter_shouldPresentNotification_(self, center, notification):
        return objc.YES

    def userNotificationCenter_didDeliverNotification_(self, center, userNotification):
        print(userNotification.userInfo)
        # print(type(userNotification.userInfo))
        # print(userNotification.userInfo.getValue_forKey_("waitForResponse"))
        # if userNotification.userInfo.getValue_forKey_("waitForResponse") == False:
        #     return

    def userNotificationCenter_didActivateNotification_(self, center, notification):
        # if notification.userInfo['uuid'] != str(id(self)):
        #     return

        additionalActionIndex = -1

        # if notification.activationType == NSUserNotificationActivationTypeAdditionalActionClicked or \
        #     notification.activationType == NSUserNotificationActivationTypeActionButtonClicked:
        #
        #     if len(notification._alternateActionButtonTitles) > 1:
        #         alternateActionIndex = notification._alternateActionIndex
        #         additionalActionIndex = int(alternateActionIndex)
        #
        #         ActionsClicked = notification._alternateActionButtonTitles[additionalActionIndex]
        AppKit.NSApp().terminate_(self)
        sys.exit(1)


    def listNotificationWithGroupID_(self, listGroupID):
        pass

    def Quit(self):
        AppKit.NSApp().terminate_(self)
        sys.exit(1)

    def bye_(self, obj):
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


if __name__ == '__main__':
    app = AppKit.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

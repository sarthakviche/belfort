package app.belfort.android;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Shows the daily streak reminder set by Bridge.remindDaily. Tapping it opens Belfort. */
public class ReminderReceiver extends BroadcastReceiver {
    static final String CHANNEL = "streak";

    @Override
    public void onReceive(Context ctx, Intent intent) {
        NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel(CHANNEL, ctx.getString(R.string.reminder_channel), NotificationManager.IMPORTANCE_DEFAULT));
        PendingIntent open = PendingIntent.getActivity(ctx, 0, new Intent(ctx, MainActivity.class), PendingIntent.FLAG_IMMUTABLE);
        Notification n = new Notification.Builder(ctx, CHANNEL)
                .setSmallIcon(R.drawable.splash_icon)
                .setContentTitle(ctx.getString(R.string.reminder_title))
                .setContentText(ctx.getString(R.string.reminder_text))
                .setContentIntent(open)
                .setAutoCancel(true)
                .build();
        nm.notify(1, n);
    }
}

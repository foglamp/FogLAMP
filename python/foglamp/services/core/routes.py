# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

from foglamp.services.core.api import auth
from foglamp.services.core.api import audit as api_audit
from foglamp.services.core.api import browser
from foglamp.services.core.api import common as api_common
from foglamp.services.core.api import configuration as api_configuration
from foglamp.services.core.api import scheduler as api_scheduler
from foglamp.services.core.api import statistics as api_statistics
from foglamp.services.core.api import backup_restore
from foglamp.services.core.api import update
from foglamp.services.core.api import service
from foglamp.services.core.api import certificate_store
from foglamp.services.core.api import support
from foglamp.services.core.api import task
from foglamp.services.core.api import asset_tracker
from foglamp.services.core.api import south
from foglamp.services.core.api import north
from foglamp.services.core.api import filters
from foglamp.services.core.api import notification
from foglamp.services.core.api.plugins import install as plugins_install, discovery as plugins_discovery
from foglamp.services.core.api.plugins import update as plugins_update
from foglamp.services.core.api.snapshot import plugins as snapshot_plugins
from foglamp.services.core.api.snapshot import table as snapshot_table
from foglamp.services.core.api import package_log

__author__ = "Ashish Jabble, Praveen Garg, Massimiliano Pinto, Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017-2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def setup(app):
    app.router.add_route('GET', '/foglamp/ping', api_common.ping)
    app.router.add_route('PUT', '/foglamp/shutdown', api_common.shutdown)
    app.router.add_route('PUT', '/foglamp/restart', api_common.restart)

    # user
    app.router.add_route('GET', '/foglamp/user', auth.get_user)
    app.router.add_route('PUT', '/foglamp/user/{id}', auth.update_user)
    app.router.add_route('PUT', '/foglamp/user/{username}/password', auth.update_password)

    # role
    app.router.add_route('GET', '/foglamp/user/role', auth.get_roles)

    # auth
    app.router.add_route('POST', '/foglamp/login', auth.login)
    app.router.add_route('PUT', '/foglamp/logout', auth.logout_me)

    # logout all active sessions
    app.router.add_route('PUT', '/foglamp/{user_id}/logout', auth.logout)

    # admin
    app.router.add_route('POST', '/foglamp/admin/user', auth.create_user)
    app.router.add_route('DELETE', '/foglamp/admin/{user_id}/delete', auth.delete_user)
    app.router.add_route('PUT', '/foglamp/admin/{user_id}/reset', auth.reset)

    # Configuration
    app.router.add_route('GET', '/foglamp/category', api_configuration.get_categories)
    app.router.add_route('POST', '/foglamp/category', api_configuration.create_category)
    app.router.add_route('GET', '/foglamp/category/{category_name}', api_configuration.get_category)
    app.router.add_route('PUT', '/foglamp/category/{category_name}', api_configuration.update_configuration_item_bulk)
    app.router.add_route('DELETE', '/foglamp/category/{category_name}', api_configuration.delete_category)
    app.router.add_route('POST', '/foglamp/category/{category_name}/children', api_configuration.create_child_category)
    app.router.add_route('GET', '/foglamp/category/{category_name}/children', api_configuration.get_child_category)
    app.router.add_route('DELETE', '/foglamp/category/{category_name}/children/{child_category}', api_configuration.delete_child_category)
    app.router.add_route('DELETE', '/foglamp/category/{category_name}/parent', api_configuration.delete_parent_category)
    app.router.add_route('GET', '/foglamp/category/{category_name}/{config_item}', api_configuration.get_category_item)
    app.router.add_route('PUT', '/foglamp/category/{category_name}/{config_item}', api_configuration.set_configuration_item)
    app.router.add_route('POST', '/foglamp/category/{category_name}/{config_item}', api_configuration.add_configuration_item)
    app.router.add_route('DELETE', '/foglamp/category/{category_name}/{config_item}/value', api_configuration.delete_configuration_item_value)
    app.router.add_route('POST', '/foglamp/category/{category_name}/{config_item}/upload', api_configuration.upload_script)
    # Scheduler
    # Scheduled_processes - As per doc
    app.router.add_route('GET', '/foglamp/schedule/process', api_scheduler.get_scheduled_processes)
    app.router.add_route('GET', '/foglamp/schedule/process/{scheduled_process_name}', api_scheduler.get_scheduled_process)

    # Schedules - As per doc
    app.router.add_route('GET', '/foglamp/schedule', api_scheduler.get_schedules)
    app.router.add_route('POST', '/foglamp/schedule', api_scheduler.post_schedule)
    app.router.add_route('GET', '/foglamp/schedule/type', api_scheduler.get_schedule_type)
    app.router.add_route('GET', '/foglamp/schedule/{schedule_id}', api_scheduler.get_schedule)
    app.router.add_route('PUT', '/foglamp/schedule/{schedule_id}/enable', api_scheduler.enable_schedule)
    app.router.add_route('PUT', '/foglamp/schedule/{schedule_id}/disable', api_scheduler.disable_schedule)

    app.router.add_route('PUT', '/foglamp/schedule/enable', api_scheduler.enable_schedule_with_name)
    app.router.add_route('PUT', '/foglamp/schedule/disable', api_scheduler.disable_schedule_with_name)

    app.router.add_route('POST', '/foglamp/schedule/start/{schedule_id}', api_scheduler.start_schedule)
    app.router.add_route('PUT', '/foglamp/schedule/{schedule_id}', api_scheduler.update_schedule)
    app.router.add_route('DELETE', '/foglamp/schedule/{schedule_id}', api_scheduler.delete_schedule)

    # Tasks - As per doc
    app.router.add_route('GET', '/foglamp/task', api_scheduler.get_tasks)
    app.router.add_route('GET', '/foglamp/task/state', api_scheduler.get_task_state)
    app.router.add_route('GET', '/foglamp/task/latest', api_scheduler.get_tasks_latest)
    app.router.add_route('GET', '/foglamp/task/{task_id}', api_scheduler.get_task)
    app.router.add_route('PUT', '/foglamp/task/{task_id}/cancel', api_scheduler.cancel_task)

    # Service
    app.router.add_route('POST', '/foglamp/service', service.add_service)
    app.router.add_route('GET', '/foglamp/service', service.get_health)
    app.router.add_route('DELETE', '/foglamp/service/{service_name}', service.delete_service)
    app.router.add_route('GET', '/foglamp/service/available', service.get_available)
    app.router.add_route('GET', '/foglamp/service/installed', service.get_installed)
    app.router.add_route('PUT', '/foglamp/service/{type}/{name}/update', service.update_service)

    # Task
    app.router.add_route('POST', '/foglamp/scheduled/task', task.add_task)
    app.router.add_route('DELETE', '/foglamp/scheduled/task/{task_name}', task.delete_task)

    # South
    app.router.add_route('GET', '/foglamp/south', south.get_south_services)

    # North
    app.router.add_route('GET', '/foglamp/north', north.get_north_schedules)

    # assets
    browser.setup(app)

    # asset tracker
    app.router.add_route('GET', '/foglamp/track', asset_tracker.get_asset_tracker_events)

    # Statistics - As per doc
    app.router.add_route('GET', '/foglamp/statistics', api_statistics.get_statistics)
    app.router.add_route('GET', '/foglamp/statistics/history', api_statistics.get_statistics_history)

    # Audit trail - As per doc
    app.router.add_route('POST', '/foglamp/audit', api_audit.create_audit_entry)
    app.router.add_route('GET', '/foglamp/audit', api_audit.get_audit_entries)
    app.router.add_route('GET', '/foglamp/audit/logcode', api_audit.get_audit_log_codes)
    app.router.add_route('GET', '/foglamp/audit/severity', api_audit.get_audit_log_severity)

    # Backup & Restore - As per doc
    app.router.add_route('GET', '/foglamp/backup', backup_restore.get_backups)
    app.router.add_route('POST', '/foglamp/backup', backup_restore.create_backup)
    app.router.add_route('GET', '/foglamp/backup/status', backup_restore.get_backup_status)
    app.router.add_route('GET', '/foglamp/backup/{backup_id}', backup_restore.get_backup_details)
    app.router.add_route('DELETE', '/foglamp/backup/{backup_id}', backup_restore.delete_backup)
    app.router.add_route('GET', '/foglamp/backup/{backup_id}/download', backup_restore.get_backup_download)
    app.router.add_route('PUT', '/foglamp/backup/{backup_id}/restore', backup_restore.restore_backup)

    # Package Update on demand
    app.router.add_route('PUT', '/foglamp/update', update.update_package)

    # certs store
    app.router.add_route('GET', '/foglamp/certificate', certificate_store.get_certs)
    app.router.add_route('POST', '/foglamp/certificate', certificate_store.upload)
    app.router.add_route('DELETE', '/foglamp/certificate/{name}', certificate_store.delete_certificate)

    # Support bundle
    app.router.add_route('GET', '/foglamp/support', support.fetch_support_bundle)
    app.router.add_route('GET', '/foglamp/support/{bundle}', support.fetch_support_bundle_item)
    app.router.add_route('POST', '/foglamp/support', support.create_support_bundle)

    # Get Syslog
    app.router.add_route('GET', '/foglamp/syslog', support.get_syslog_entries)

    # Package logs
    app.router.add_route('GET', '/foglamp/package/log', package_log.get_logs)
    app.router.add_route('GET', '/foglamp/package/log/{name}', package_log.get_log_by_name)

    # Plugins (install, discovery, update)
    app.router.add_route('GET', '/foglamp/plugins/installed', plugins_discovery.get_plugins_installed)
    app.router.add_route('GET', '/foglamp/plugins/available', plugins_discovery.get_plugins_available)
    app.router.add_route('POST', '/foglamp/plugins', plugins_install.add_plugin)
    app.router.add_route('PUT', '/foglamp/plugins/{type}/{name}/update', plugins_update.update_plugin)

    # Filters 
    app.router.add_route('POST', '/foglamp/filter', filters.create_filter)
    app.router.add_route('PUT', '/foglamp/filter/{user_name}/pipeline', filters.add_filters_pipeline)
    app.router.add_route('GET', '/foglamp/filter/{user_name}/pipeline', filters.get_filter_pipeline)
    app.router.add_route('GET', '/foglamp/filter/{filter_name}', filters.get_filter)
    app.router.add_route('GET', '/foglamp/filter', filters.get_filters)
    app.router.add_route('DELETE', '/foglamp/filter/{user_name}/pipeline', filters.delete_filter_pipeline)
    app.router.add_route('DELETE', '/foglamp/filter/{filter_name}', filters.delete_filter)

    # Notification
    app.router.add_route('GET', '/foglamp/notification', notification.get_notifications)
    app.router.add_route('GET', '/foglamp/notification/plugin', notification.get_plugin)
    app.router.add_route('GET', '/foglamp/notification/type', notification.get_type)
    app.router.add_route('GET', '/foglamp/notification/{notification_name}', notification.get_notification)
    app.router.add_route('POST', '/foglamp/notification', notification.post_notification)
    app.router.add_route('PUT', '/foglamp/notification/{notification_name}', notification.put_notification)
    app.router.add_route('DELETE', '/foglamp/notification/{notification_name}', notification.delete_notification)

    # Snapshot plugins
    app.router.add_route('GET', '/foglamp/snapshot/plugins', snapshot_plugins.get_snapshot)
    app.router.add_route('POST', '/foglamp/snapshot/plugins', snapshot_plugins.post_snapshot)
    app.router.add_route('PUT', '/foglamp/snapshot/plugins/{id}', snapshot_plugins.put_snapshot)
    app.router.add_route('DELETE', '/foglamp/snapshot/plugins/{id}', snapshot_plugins.delete_snapshot)

    # Snapshot config
    app.router.add_route('GET', '/foglamp/snapshot/category', snapshot_table.get_snapshot)
    app.router.add_route('POST', '/foglamp/snapshot/category', snapshot_table.post_snapshot)
    app.router.add_route('PUT', '/foglamp/snapshot/category/{id}', snapshot_table.put_snapshot)
    app.router.add_route('DELETE', '/foglamp/snapshot/category/{id}', snapshot_table.delete_snapshot)
    app.router.add_route('GET', '/foglamp/snapshot/schedule', snapshot_table.get_snapshot)
    app.router.add_route('POST', '/foglamp/snapshot/schedule', snapshot_table.post_snapshot)
    app.router.add_route('PUT', '/foglamp/snapshot/schedule/{id}', snapshot_table.put_snapshot)
    app.router.add_route('DELETE', '/foglamp/snapshot/schedule/{id}', snapshot_table.delete_snapshot)

    # enable cors support
    enable_cors(app)

    # enable a live debugger (watcher) for requests, see https://github.com/aio-libs/aiohttp-debugtoolbar
    # this will neutralize error middleware
    # Note: pip install aiohttp_debugtoolbar

    # enable_debugger(app)


def enable_cors(app):
    """ implements Cross Origin Resource Sharing (CORS) support """
    import aiohttp_cors

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)


def enable_debugger(app):
    """ provides a debug toolbar for server requests """
    import aiohttp_debugtoolbar

    # dev mode only
    # this will be served at API_SERVER_URL/_debugtoolbar
    aiohttp_debugtoolbar.setup(app)

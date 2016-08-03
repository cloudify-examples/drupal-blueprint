$conf['cache_backends'][] = 'sites/all/modules/memcache/memcache.inc';
$conf['lock_inc'] = 'sites/all/modules/memcache/memcache-lock.inc';
$conf['memcache_stampede_protection'] = TRUE;
$conf['cache_default_class'] = 'MemCacheDrupal';

// The 'cache_form' bin must be assigned no non-volatile storage.
$conf['cache_class_cache_form'] = 'DrupalDatabaseCache';

// Don't bootstrap the database when serving pages from the cache.
$conf['page_cache_without_database'] = TRUE;
$conf['page_cache_invoke_hooks'] = FALSE;

$conf['memcache_servers'] = array('MEMCACHE_HOST_IP:MEMCACHE_PORT' => 'default',
	'MEMCACHE_HOST_IP:MEMCACHE_PORT' => 'pages',
	'MEMCACHE_HOST_IP:MEMCACHE_PORT' => 'blocks',
	'MEMCACHE_HOST_IP:MEMCACHE_PORT' => 'filters',
	'MEMCACHE_HOST_IP:MEMCACHE_PORT' => 'menus');
$conf['memcache_bins'] = array('cache' => 'default',
 'cache_page' => 'pages',
 'cache_block' => 'blocks',
 'cache_filter' => 'filters',
 'cache_menu' => 'menus');
			
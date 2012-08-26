/**
 * Use require('dns') to access this module.
 */
var dns = {};

/**
 * Resolves a domain (e.g. 'google.com') into an array of the record types
 * specified by rrtype. Valid rrtypes are A (IPV4 addresses), AAAA (IPV6
 * addresses), MX (mail exchange records), TXT (text records), SRV (SRV
 * records), PTR (used for reverse IP lookups), NS (name server records)
 * and CNAME (canonical name records).
 * @param domain
 * @param rrtype='A'
 * @param callback
 */
dns.resolve = function(domain, rrtype, callback) {}

/**
 * Reverse resolves an ip address to an array of domain names.
 * @param ip
 * @param callback
 */
dns.reverse = function(ip, callback) {}

/**
 * The same as dns.resolve(), but only for mail exchange queries (MX
 * records).
 * @param domain
 * @param callback
 */
dns.resolveMx = function(domain, callback) {}

/**
 * The same as dns.resolve(), but only for text queries (TXT records).
 * addresses is an array of the text records available for domain (e.g.,
 * ['v=spf1 ip4:0.0.0.0 ~all']).
 * @param domain
 * @param callback
 */
dns.resolveTxt = function(domain, callback) {}

/**
 * The same as dns.resolve(), but only for IPv4 queries (A records).
 * addresses is an array of IPv4 addresses (e.g. ['74.125.79.104',
 * '74.125.79.105', '74.125.79.106']).
 * @param domain
 * @param callback
 */
dns.resolve4 = function(domain, callback) {}

/**
 * The same as dns.resolve(), but only for service records (SRV records).
 * addresses is an array of the SRV records available for domain.
 * Properties of SRV records are priority, weight, port, and name (e.g.,
 * [{'priority': 10, {'weight': 5, 'port': 21223, 'name':
 * 'service.example.com'}, ...]).
 * @param domain
 * @param callback
 */
dns.resolveSrv = function(domain, callback) {}

/**
 * The same as dns.resolve4() except for IPv6 queries (an AAAA query).
 * @param domain
 * @param callback
 */
dns.resolve6 = function(domain, callback) {}

/**
 * Resolves a domain (e.g. 'google.com') into the first found A (IPv4) or
 * AAAA (IPv6) record.
 * @param domain
 * @param family=null
 * @param callback
 */
dns.lookup = function(domain, family, callback) {}

/**
 * The same as dns.resolve(), but only for canonical name records (CNAME
 * records). addresses is an array of the canonical name records available
 * for domain (e.g., ['bar.example.com']).
 * @param domain
 * @param callback
 */
dns.resolveCname = function(domain, callback) {}

/**
 * The same as dns.resolve(), but only for name server records (NS
 * records). addresses is an array of the name server records available for
 * domain (e.g., ['ns1.example.com', 'ns2.example.com']).
 * @param domain
 * @param callback
 */
dns.resolveNs = function(domain, callback) {}


exports = dns;


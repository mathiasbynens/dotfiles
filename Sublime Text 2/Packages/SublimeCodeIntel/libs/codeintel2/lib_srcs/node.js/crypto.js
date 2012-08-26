/**
 * Use require('crypto') to access this module.
 */
var crypto = {};

crypto.Hash = function() {}
crypto.Hash.prototype = {}
/**
 * Updates the hash content with the given data. This can be called many
 * times with new data as it is streamed.
 * @param data
 */
crypto.Hash.prototype.update = function(data) {}
/**
 * Calculates the digest of all of the passed data to be hashed. The
 * encoding can be 'hex', 'binary' or 'base64'.
 * @param encoding='binary'
 */
crypto.Hash.prototype.digest = function(encoding) {}

/**
 * Creates and returns a cipher object, with the given algorithm and key.
 * @param algorithm
 * @param key
 * @returns Cipher
 */
crypto.createCipher = function(algorithm, key) {}

/**
 * Creates and returns a hmac object, a cryptographic hmac with the given
 * algorithm and key.
 * @param algorithm
 * @param key
 * @returns Hmac
 */
crypto.createHmac = function(algorithm, key) {}

crypto.Verify = function() {}
crypto.Verify.prototype = {}
/**
 * Verifies the signed data by using the cert which is a string containing
 * the PEM encoded certificate, and signature, which is the previously
 * calculates signature for the data, in the signature_format which can be
 * 'binary', 'hex' or 'base64'.
 * @param cert
 * @param signature
 * @param signature_format='binary'
 */
crypto.Verify.prototype.verify = function(cert, signature, signature_format) {}
/**
 * Updates the verifier object with data. This can be called many times
 * with new data as it is streamed.
 * @param data
 */
crypto.Verify.prototype.update = function(data) {}

/**
 * Creates a credentials object, with the optional details being a
 * dictionary with keys:
 * @param details
 */
crypto.createCredentials = function(details) {}

/**
 * Creates and returns a signing object, with the given algorithm. On
 * recent OpenSSL releases, openssl list-public-key-algorithms will display
 * the available signing algorithms. Examples are 'RSA-SHA256'.
 * @param algorithm
 * @returns Sign
 */
crypto.createSign = function(algorithm) {}

crypto.Sign = function() {}
crypto.Sign.prototype = {}
/**
 * Updates the signer object with data. This can be called many times with
 * new data as it is streamed.
 * @param data
 */
crypto.Sign.prototype.update = function(data) {}
/**
 * Calculates the signature on all the updated data passed through the
 * signer. private_key is a string containing the PEM encoded private key
 * for signing.
 * @param private_key
 * @param output_format='binary'
 */
crypto.Sign.prototype.sign = function(private_key, output_format) {}

crypto.Cipher = function() {}
crypto.Cipher.prototype = {}
/**
 * Updates the cipher with data, the encoding of which is given in
 * input_encoding and can be 'utf8', 'ascii' or 'binary'. The
 * output_encoding specifies the output format of the enciphered data, and
 * can be 'binary', 'base64' or 'hex'.
 * @param data
 * @param input_encoding='binary'
 * @param output_encoding='binary'
 */
crypto.Cipher.prototype.update = function(data, input_encoding, output_encoding) {}
/**
 * Returns any remaining enciphered contents, with output_encoding being
 * one of: 'binary', 'ascii' or 'utf8'.
 * @param output_encoding='binary'
 */
crypto.Cipher.prototype.final = function(output_encoding) {}

/**
 * Creates and returns a hash object, a cryptographic hash with the given
 * algorithm which can be used to generate hash digests.
 * @param algorithm
 * @returns Hash
 */
crypto.createHash = function(algorithm) {}

crypto.Decipher = function() {}
crypto.Decipher.prototype = {}
/**
 * Updates the decipher with data, which is encoded in 'binary', 'base64'
 * or 'hex'. The output_decoding specifies in what format to return the
 * deciphered plaintext: 'binary', 'ascii' or 'utf8'.
 * @param data
 * @param input_encoding='binary'
 * @param output_encoding='binary'
 */
crypto.Decipher.prototype.update = function(data, input_encoding, output_encoding) {}
/**
 * Returns any remaining plaintext which is deciphered, with
 * output_encoding' being one of: 'binary', 'ascii' or 'utf8'`.
 * @param output_encoding='binary'
 */
crypto.Decipher.prototype.final = function(output_encoding) {}

crypto.Credentials = function() {}
crypto.Credentials.prototype = {}

/**
 * Creates and returns a decipher object, with the given algorithm and key.
 * This is the mirror of the cipher object above.
 * @param algorithm
 * @param key
 * @returns Decipher
 */
crypto.createDecipher = function(algorithm, key) {}

/**
 * Creates and returns a verification object, with the given algorithm.
 * This is the mirror of the signing object above.
 * @param algorithm
 * @returns Verify
 */
crypto.createVerify = function(algorithm) {}

crypto.Hmac = function() {}
crypto.Hmac.prototype = {}
/**
 * Update the hmac content with the given data. This can be called many
 * times with new data as it is streamed.
 * @param data
 */
crypto.Hmac.prototype.update = function(data) {}
/**
 * Calculates the digest of all of the passed data to the hmac. The
 * encoding can be 'hex', 'binary' or 'base64'.
 * @param encoding='binary'
 */
crypto.Hmac.prototype.digest = function(encoding) {}


exports = crypto;


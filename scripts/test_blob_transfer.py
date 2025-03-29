#!/usr/bin/env python3
"""
Test tool for BlobTransfer functionality.

This script can be used to test the BlobTransfer implementation against
real HTTP servers, with and without range request support.
"""

import argparse
import os
import sys
import time
from urllib.parse import urlparse

import urllib3

from domino_data.transfer import BlobTransfer
from domino_data.logging import logger


def test_download(url, output_file, max_workers=5, chunk_size=16*1024*1024, verify_ssl=True):
    """
    Test downloading a file using BlobTransfer.
    
    Args:
        url: The URL to download from
        output_file: Path to save the downloaded file
        max_workers: Maximum number of parallel workers
        chunk_size: Size of each chunk in bytes
        verify_ssl: Whether to verify SSL certificates
    
    Returns:
        dict with test results
    """
    start_time = time.time()
    
    # Create HTTP pool manager with appropriate SSL verification
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED' if verify_ssl else 'CERT_NONE')
    
    # Open the output file
    with open(output_file, 'wb') as f:
        # Create the BlobTransfer object
        transfer = BlobTransfer(
            url=url,
            destination=f,
            max_workers=max_workers,
            chunk_size=chunk_size,
            http=http
        )
    
    end_time = time.time()
    download_time = end_time - start_time
    
    # Get file size
    file_size = os.path.getsize(output_file)
    
    # Calculate speed
    speed_mbps = (file_size / 1024 / 1024) / download_time if download_time > 0 else 0
    
    return {
        'url': url,
        'file_size': file_size,
        'download_time': download_time,
        'speed_mbps': speed_mbps,
        'supports_range': transfer.supports_range,
        'method': 'Parallel' if transfer.supports_range else 'Sequential'
    }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Test BlobTransfer functionality')
    parser.add_argument('url', help='URL to download')
    parser.add_argument('--output', '-o', help='Output file (default: derived from URL)')
    parser.add_argument('--workers', '-w', type=int, default=5, help='Maximum number of workers')
    parser.add_argument('--chunk-size', '-c', type=int, default=16*1024*1024, 
                        help='Chunk size in bytes')
    parser.add_argument('--no-verify-ssl', action='store_true', 
                        help='Disable SSL certificate verification')
    
    args = parser.parse_args()
    
    # Derive output filename from URL if not specified
    if not args.output:
        parsed_url = urlparse(args.url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = 'download.bin'
        args.output = filename
    
    print(f"Downloading {args.url} to {args.output}...")
    
    try:
        results = test_download(
            url=args.url,
            output_file=args.output,
            max_workers=args.workers,
            chunk_size=args.chunk_size,
            verify_ssl=not args.no_verify_ssl
        )
        
        print("\nDownload Results:")
        print(f"URL: {results['url']}")
        print(f"File Size: {results['file_size'] / 1024 / 1024:.2f} MB")
        print(f"Download Time: {results['download_time']:.2f} seconds")
        print(f"Speed: {results['speed_mbps']:.2f} MB/s")
        print(f"Range Requests Supported: {results['supports_range']}")
        print(f"Download Method: {results['method']}")
        
        print(f"\nFile successfully downloaded to {args.output}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

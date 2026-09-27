"""Compatibility entry point. V2 DOM/layout checks now use a real HTTP browser
and isolated versioned fixtures instead of assuming six permanent news items.
"""
from browser_v2 import main
if __name__=='__main__':main()

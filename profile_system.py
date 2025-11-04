"""
Profile the flexibility tracker system using cProfile
"""
import cProfile
import pstats
from pstats import SortKey
import sys

# Your imports
from core.pose_estimator import PoseEstimator
from core.multi_pose_analyzer import MultiPoseAnalyzer
from core.session import PoseSession
from gui.app import GUIApp

def run_profiled_app():
    """Run app with profiling enabled"""
    estimator = PoseEstimator()
    analyzer = MultiPoseAnalyzer() 
    session = PoseSession(pose_name="Front Split")
    
    app = GUIApp(estimator, analyzer, session)
    app.mainloop()

if __name__ == "__main__":
    # Profile the application
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        run_profiled_app()
    except KeyboardInterrupt:
        print("\nProfiling interrupted by user")
    
    profiler.disable()
    
    # Print results
    print("\n" + "="*80)
    print("PROFILING RESULTS")
    print("="*80)
    
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats(SortKey.CUMULATIVE)
    
    print("\nTop 20 functions by cumulative time:")
    stats.print_stats(20)
    
    # Save to file
    stats.dump_stats('profiling_output.prof')
    print("\nDetailed results saved to: profiling_output.prof")
    print("View with: python -m pstats profiling_output.prof")
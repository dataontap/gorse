
#!/bin/bash

# Batch migration runner for Firebase users
# This script runs the migration for all 36 batches

echo "Starting Firebase user migration for 36 batches..."
echo "Each batch contains 1000 users"
echo ""

# Initialize counters
total_success=0
total_failed=0
completed_batches=0

# Run migration for each batch
for i in {1..36}
do
    echo "===================="
    echo "Running batch $i of 36"
    echo "===================="
    
    # Run the migration for this batch
    python run_migration.py $i
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Batch $i completed successfully"
        ((completed_batches++))
    else
        echo "Batch $i failed"
    fi
    
    # Add a small delay between batches to avoid rate limiting
    if [ $i -lt 36 ]; then
        echo "Waiting 5 seconds before next batch..."
        sleep 5
    fi
    
    echo ""
done

echo "===================="
echo "Migration Summary"
echo "===================="
echo "Completed batches: $completed_batches/36"
echo ""
echo "Check migration_results.json for detailed results"
echo "Check individual batch logs above for specific success/failure counts"
